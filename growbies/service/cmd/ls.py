import os
import re
import logging
import shlex
import subprocess

from growbies.db.models.device import Device, Devices, ConnectionState
from growbies.db.engine import get_db_engine
from growbies.utils.paths import InstallPaths
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

def execute() -> Devices:
    discovered_devices = Devices()
    _discover_info(discovered_devices)
    return get_db_engine().device.merge_with_discovered(discovered_devices)

def _discover_info(devices: Devices):
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
        cmd = f'udevadm info --attribute-walk {path}'
        try:
            proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, check=True, encoding='utf-8',
                                  env=env)
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
