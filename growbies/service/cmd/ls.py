import os
import re
import logging
import queue
import shlex
import subprocess
import threading
import time
from collections.abc import Callable
from enum import StrEnum

import pyudev

from growbies.common.utils.paths import InstallPaths
from growbies.db.engine import get_db_engine
from growbies.db.models.device import Device, DeviceEngine, Devices, ConnectionState
from growbies.service.common import ServiceCmdError
from growbies.session import get_session

logger = logging.getLogger(__name__)

class SupportedVidPid:
    ESPRESSIF_DEBUG = (0x303a, 0x1001)
    FTDI_FT232 = (0x0403, 0x6001)

    all_ = (ESPRESSIF_DEBUG, FTDI_FT232)

class DiscoveredDevice:
    vid = None
    pid = None
    serial = None

    def reset(self):
        self.vid = None
        self.pid = None
        self.serial = None

    def valid(self) -> bool:
        return (self.vid, self.pid) in SupportedVidPid.all_ and self.serial

class DeviceMonitor(threading.Thread):
    DISCOVER_DEVICES_POLL_SEC = 30
    UDEV_EVENT_POLL_SEC = 0.25
    UDEV_TIMEOUT_SEC = 5
    RESCAN_DEFAULT_TIMEOUT_SEC = 30
    # the shutdown logic implemented assures interruption inter-device info discovery (
    # UDEV_TIMEOUT_SEC) and additional shutdown overhead in python (+1)
    STOP_TIMEOUT_SEC = UDEV_TIMEOUT_SEC + 1

    class Task(StrEnum):
        EXIT = 'exit'
        RESCAN = 'rescan'
        NOOP = 'no-operation'

    class TaskRequest:
        def __init__(self, task_type: 'DeviceMonitor.Task'):
            self._type = task_type
            self._queue = queue.Queue(maxsize=1)

        @property
        def type(self) -> 'DeviceMonitor.Task':
            return self._type

        @property
        def queue(self) -> queue.Queue:
            return self._queue

        def get_result(self, timeout: int):
            try:
                return self._queue.get(timeout=timeout)
            except queue.Empty:
                raise ServiceCmdError(f'Timeout of {timeout} seconds waiting for task "'
                                      f'{self._type}".')

    def __init__(self, callbacks: list[Callable]):
        super().__init__(daemon=True)
        self._callbacks = callbacks
        self._devices = Devices()
        self._devices_lock = threading.Lock()
        self._queue = queue.Queue()
        self._stop_event = threading.Event()

    @property
    def devices(self) -> Devices:
        with self._devices_lock:
            return self._get_shallow_copy_of_devices()

    def stop(self):
        self._stop_event.set()
        self._queue.put(self.TaskRequest(self.Task.EXIT))
        self.join(timeout=self.STOP_TIMEOUT_SEC)
        if self.is_alive():
            logger.warning(f'Timed out of {self.STOP_TIMEOUT_SEC} seconds waiting for device '
                           f'monitor thread to stop.')

    def rescan(self) -> Devices:
        task = self.TaskRequest(self.Task.RESCAN)
        self._queue.put(task)
        return task.get_result(DeviceMonitor.RESCAN_DEFAULT_TIMEOUT_SEC)

    def run(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='tty')
        # udev events will enqueue inter-`monitor.poll` calls due to the `monitor.start` method.
        monitor.start()

        db_engine = get_db_engine()

        last_discovery = time.monotonic() - self.DISCOVER_DEVICES_POLL_SEC

        while True:
            try:
                task = self._queue.get(timeout=self.UDEV_EVENT_POLL_SEC)
            except queue.Empty:
                task = self.TaskRequest(self.Task.NOOP)

            if task.type == self.Task.EXIT or self._stop_event.is_set():
                break

            events = []

            while True:
                event = monitor.poll(timeout=0)
                if event is None:
                    break
                events.append(event)

            for event in events:
                logger.debug(
                    'udev event: action=%s, node=%s',
                    event.action,
                    event.device_node,
                )

            now = time.monotonic()
            if (events or
                now - last_discovery >= self.DISCOVER_DEVICES_POLL_SEC or
                task.type == self.Task.RESCAN):
                new_devices = self._discover_devices()

                with self._devices_lock:
                    changed = not self._devices.have_same_discovery_info(new_devices)
                    if changed:
                        self._devices = new_devices

                    if task.type == self.Task.RESCAN:
                        devices = self._get_shallow_copy_of_devices()

                if changed:
                    db_engine.device.merge_with_discovered(new_devices)
                    self._notify()

                if task.type == self.Task.RESCAN:
                    task.queue.put(devices)

                last_discovery = time.monotonic()

    def _discover_devices(self) -> Devices:
        """
        returns an empty device list on user cancellation
        """
        devices = Devices()

        block_start_re = re.compile(r"^\s*looking at device '")
        vid_re = re.compile(r'.*idVendor.*==\"([0-9a-fA-F]+)\"')
        pid_re = re.compile(r'.*idProduct.*==\"([0-9a-fA-F]+)\"')
        serial_re = re.compile(r'.*serial.*==\"([^\"]+)\"')

        paths = list(InstallPaths.DEV.value.glob('ttyUSB*'))
        paths.extend(InstallPaths.DEV.value.glob('ttyACM*'))

        session = get_session()

        env = os.environ.copy()
        env['SYSTEMD_PAGER'] = 'cat'
        for path in paths:
            if self._stop_event.is_set():
                return Devices()
            cmd = f'udevadm info --attribute-walk {path}'
            try:
                proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, check=True, encoding='utf-8',
                                      env=env, timeout=self.UDEV_TIMEOUT_SEC)
            except subprocess.TimeoutExpired:
                logger.error('Timed out discovering device at %s', path)
                continue
            except subprocess.CalledProcessError as err:
                logger.error(err.stderr)
                logger.exception(err)
                continue

            discovered_device = DiscoveredDevice()

            for line in proc.stdout.splitlines():
                if block_start_re.match(line):
                    discovered_device.reset()

                vid_search = vid_re.search(line)
                if vid_search:
                    discovered_device.vid = int(vid_search.group(1), 16)

                pid_search = pid_re.search(line)
                if pid_search:
                    discovered_device.pid = int(pid_search.group(1), 16)

                serial_search = serial_re.search(line)
                if serial_search:
                    discovered_device.serial = serial_search.group(1)

                if discovered_device.valid():
                    devices.append(Device(gateway=session.gateway.id,
                                          vid=discovered_device.vid,
                                          pid=discovered_device.pid,
                                          serial=discovered_device.serial,
                                          path=str(path), state=ConnectionState.DISCOVERED))
                    break
        return devices

    def _get_shallow_copy_of_devices(self) -> Devices:
        return Devices(elements=list(self._devices))

    def _notify(self):
        for callback in self._callbacks:
            callback()

# Application global singleton
_device_monitor: DeviceMonitor | None = None
_device_monitor_lock = threading.Lock()

def make_device_monitor_singleton(callbacks: list[Callable]):
    global _device_monitor

    with _device_monitor_lock:
        if _device_monitor is not None:
            raise ServiceCmdError(f'Attempted creation of multiple device monitors.')
        else:
            _device_monitor = DeviceMonitor(callbacks)
            # noinspection PyUnresolvedReferences
            _device_monitor.start()

def get_device_monitor_singleton() -> DeviceMonitor:
    with _device_monitor_lock:
        if _device_monitor is None:
            raise ServiceCmdError(
                'The device monitor singleton needs to be made before accessed.'
            )
        return _device_monitor

def stop_device_monitor_singleton():
    global _device_monitor
    with _device_monitor_lock:
        device_monitor = _device_monitor

    if device_monitor is not None:
        device_monitor.stop()
