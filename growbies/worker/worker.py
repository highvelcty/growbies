import errno
import logging
from queue import Queue, Empty, Full
from threading import Event, Thread
from typing import Optional

from serial.serialutil import SerialException

from growbies.db.engine import get_db_engine
from growbies.intf import Intf
from growbies.intf.cmd import TDeviceCmd
from growbies.intf.common import BaseStructure
from growbies.intf.resp import (DeviceResp, DataPointDeviceResp,
                                DeviceError, ErrorDeviceResp, RespPacketHdr, TDeviceResp)
from growbies.session import log
from growbies.utils.types import DeviceID_t, WorkerID_t
from growbies.service.resp.structs import ServiceCmdError

logger = logging.getLogger(__name__)

class PipeCmd:
    STOP = b'stop'
    WAKE = b'wake'

class Worker(Thread):
    _RECONNECT_RETRY_DELAY_SECONDS = 3
    _RECONNECT_RETRY_POLLING_SECONDS = 0.1
    _ASYNC_RESPONSES = (DataPointDeviceResp, ErrorDeviceResp)
    _PIPE_READ_BYTES = 1024
    _DEFAULT_CMD_TIMEOUT_SECONDS = 3
    _RESP_Q_TIMEOUT_SECONDS = 0.1
    _JOIN_TIMEOUT_SECONDS = 3

    def __init__(self, device_id: DeviceID_t):
        super().__init__()
        self._out_queue = Queue()
        self._engine = get_db_engine().devices.get_engine(device_id)
        self._device = self._engine.get(device_id)
        self._intf: Optional[Intf] = None
        self._stop_event = Event()
        self._reconnect_attempt = 0

    @property
    def id(self) -> WorkerID_t:
        return self._device.id

    def cmd(self, cmd: TDeviceCmd, timeout: Optional[float] = _DEFAULT_CMD_TIMEOUT_SECONDS) \
            -> TDeviceResp | ServiceCmdError:
        """
        raises:
            :class:`DeviceError`
            :class:`ServiceCmdError`
        """
        if not self._intf:
            raise ServiceCmdError(f'Worker thread for {self.name} is not ready.')

        self._intf.send_cmd(cmd)
        resp = self._out_queue.get(block=True, timeout=timeout)

        if isinstance(resp, ErrorDeviceResp):
            raise DeviceError(resp.error)

        return resp

    @property
    def name(self):
        return f'{self._device.serial}'

    def stop(self):
        self._stop_event.set()
        self.join(self._JOIN_TIMEOUT_SECONDS)
        if self.is_alive():
            logger.error(f'Thread did not die after {self._JOIN_TIMEOUT_SECONDS} seconds.')

    def _connect(self) -> bool:
        try:
            self._intf = Intf(port=self._device.path, thread_name=f'{self.name}_SLIP')
        except (SerialException, PermissionError) as err:
            # SerialException may or may not have errno
            errno_ = getattr(err, 'errno', None)
            if errno_ == errno.ENOENT:
                logger.error(f'Serial port not found: {self._device.path}.')
            elif errno_ == errno.EACCES:
                logger.error(f'Serial port access denied: {self._device.path}')
            elif errno_ == errno.EBUSY:
                logger.error(f'Serial port busy: {self._device.path}')
            elif errno_ == errno.ENODEV:
                logger.error(f'Serial port no such device: {self._device.path}')
            else:
                logger.exception(err)
            return False

        self._intf.start()
        self._reconnect_attempt = 0
        return True

    def _disconnect(self):
        if self._intf:
            self._intf.stop()
            self._intf = None

    @staticmethod
    def _process_async(hdr: RespPacketHdr, resp: TDeviceResp | ErrorDeviceResp):
        if hdr.type == DeviceResp.ERROR:
            resp: ErrorDeviceResp
            logger.error(f'Received asynchronous error response with '
                         f'error code {resp.error} 0x{resp.error:X}')
        elif hdr.type == DeviceResp.DATAPOINT:
            logger.info(f'Received asynchronous {hdr.type} response.')
        else:
            logger.error(f'Invalid response type received: {hdr.type}.')

    def _service_cmds(self):
        while not self._stop_event.is_set() and self._intf and self._intf.is_alive():
            try:
               hdr, resp = self._intf.recv_resp(timeout=self._RESP_Q_TIMEOUT_SECONDS)
               hdr: RespPacketHdr
               resp: BaseStructure

            except Empty:
                continue
            except Exception as err:
                logger.exception(err)
                continue

            if resp is None:
                continue
            if hdr.id:
                logger.info(f'Received synchronous {hdr.type} response.')
                self._put_no_wait(resp)
            else:
                self._process_async(hdr, resp)

        if self._intf and not self._intf.is_alive():
            logger.error(f'SLIP thread died.')

    def _do_report_reconnect(self) -> bool:
        if self._reconnect_attempt <= 10:
            return True
        elif self._reconnect_attempt <= 100:
            return not bool(self._reconnect_attempt % 10)
        else:
            return not bool(self._reconnect_attempt % 100)

    def _put_no_wait(self, resp: TDeviceResp | DeviceError | ServiceCmdError):
        try:
            self._out_queue.put_nowait(resp)
        except Full:
            logger.error('Worker output queue full.')

    def run(self):
        log.thread_local.name = self.name
        logger.info(f'Thread start.')

        # Outer loop
        while not self._stop_event.is_set():
            try:
                self._engine.init_start_connection()
                logger.info('Device connecting.')
                if self._connect():
                    self._engine.set_connected()
                    logger.info('Device connected.')

                    # Inner loop
                    self._service_cmds()
            except Exception as err:
                logger.exception(err)

            # Cleanup
            self._disconnect()
            logger.info('Device disconnected.')
            self._engine.clear_connected()

            # Reconnect
            if not self._stop_event.is_set():
                self._engine.set_error()
                if not self._stop_event.wait(self._RECONNECT_RETRY_DELAY_SECONDS):
                    self._reconnect_attempt += 1
                    if self._do_report_reconnect():
                        logger.info(f'Reconnection attempt {self._reconnect_attempt}')

        logger.info(f'Thread exit.')
