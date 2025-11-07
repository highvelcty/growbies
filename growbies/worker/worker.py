import errno
import logging
import queue
import time
from queue import Queue, Empty, Full
from threading import Event, Thread
from typing import Optional

from serial.serialutil import SerialException

from growbies.constants import UINT8_MAX
from growbies.db.engine import get_db_engine
from growbies.device.cmd import TDeviceCmd
from growbies.device.resp import (DeviceRespOp, DeviceError, DataPoint, ErrorDeviceResp,
                                  RespPacketHdr, TDeviceResp)
from growbies.service.common import ServiceCmdError
from growbies.session import log
from growbies.utils.types import DeviceID, WorkerID
from growbies.worker.slip import SerialIntf

logger = logging.getLogger(__name__)

class PipeCmd:
    STOP = b'stop'
    WAKE = b'wake'

class Worker(Thread):
    _RECONNECT_RETRY_DELAY_SECONDS = 3
    _RECONNECT_RETRY_POLLING_SECONDS = 0.1
    _PIPE_READ_BYTES = 1024
    _DEFAULT_CMD_TIMEOUT_SECONDS = 3
    _RESP_Q_TIMEOUT_SECONDS = 0.1
    _JOIN_TIMEOUT_SECONDS = 3

    def __init__(self, device_id: DeviceID):
        super().__init__()
        self._device_id = device_id
        self._out_queue = Queue()
        self._db_engine = get_db_engine()
        self._device = self._db_engine.device.get(device_id)
        self._intf: Optional[SerialIntf] = None
        self._stop_event = Event()
        self._reconnect_attempt = 0
        self._cmd_id = 1

    @property
    def id(self) -> WorkerID:
        return self._device.id

    @property
    def name(self):
        return f'{self._device.serial}'

    def cmd(self, cmd: TDeviceCmd, timeout: Optional[float] = _DEFAULT_CMD_TIMEOUT_SECONDS) \
            -> TDeviceResp:
        """
        raises:
            :class:`DeviceError`
            :class:`ServiceCmdError`
        """
        exc_timeout = ServiceCmdError(f'Timeout {timeout} seconds waiting for response.')

        if not self._intf:
            raise ServiceCmdError(f'Worker thread for {self.name} is not ready.')

        self._intf.send_cmd(cmd, self._next_cmd_id())

        startt = time.time()
        elapsed = 0
        while elapsed < timeout:
            try:
                item = self._out_queue.get(block=True, timeout=timeout - elapsed)
            except queue.Empty:
                raise exc_timeout

            if isinstance(item, Exception):
                raise item

            hdr, resp = item

            if isinstance(resp, ErrorDeviceResp):
                raise DeviceError(resp.error)

            if hdr.id != self._cmd_id:
                logger.warning(f'Out of sync serial response. Expected ID {self._cmd_id}, '
                               f'observed {hdr.id}.')
                elapsed = time.time() - startt
                continue

            return resp

        raise exc_timeout

    def stop(self):
        self._stop_event.set()
        self.join(self._JOIN_TIMEOUT_SECONDS)
        if self.is_alive():
            logger.error(f'Thread did not die after {self._JOIN_TIMEOUT_SECONDS} seconds.')

    def _connect(self) -> bool:
        try:
            self._intf = SerialIntf(port=self._device.path, thread_name=f'{self.name}_SLIP')
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

    def _next_cmd_id(self) -> int:
        # Increment and wrap between 1–255
        self._cmd_id = (self._cmd_id % UINT8_MAX) + 1
        return self._cmd_id

    def _process_async(self, hdr: RespPacketHdr, resp: TDeviceResp | ErrorDeviceResp):
        if hdr.type == DeviceRespOp.ERROR:
            resp: ErrorDeviceResp
            logger.error(f'Received asynchronous error response with '
                         f'error code {resp.error} 0x{resp.error:X}')
        elif hdr.type == DeviceRespOp.DATAPOINT:
            resp: DataPoint
            tare_id = self._db_engine.tare.insert(resp.tare).id
            datapoint = self._db_engine.datapoint.insert(self._device_id, tare_id, resp)
            for sess in self._db_engine.session.get_active_by_device_id(self._device_id):
                self._db_engine.link.session_datapoint.add(sess.id, datapoint.id)

            logger.info(f'Received asynchronous {hdr.type} response.')
        else:
            logger.error(f'Invalid response type received: {hdr.type}.')

    def _service_cmds(self):
        while not self._stop_event.is_set() and self._intf and self._intf.is_alive():
            try:
               hdr, resp = self._intf.recv_resp(timeout=self._RESP_Q_TIMEOUT_SECONDS)
               hdr: RespPacketHdr
               resp: TDeviceResp

            except Empty:
                continue
            except Exception as err:
                # meyere, need to handle errors from async/sync
                self._put_no_wait(err)
                continue

            if resp is None:
                continue
            if hdr.id == self._cmd_id:
                logger.info(f'Received synchronous {hdr.type} response.')
                self._put_no_wait((hdr, resp))
            elif hdr.id != self._cmd_id:
                logger.warning(f'Received out of sequence response. Expected response ID '
                               f'{self._cmd_id}, observed {hdr.id}.')
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

    def _put_no_wait(self, item: tuple[RespPacketHdr, TDeviceResp] | Exception):
        try:
            if isinstance(item, Exception):
                self._out_queue.put_nowait(item)
            else:
                hdr, resp = item
                self._out_queue.put_nowait((type(hdr).from_buffer_copy(hdr),
                                            type(resp).from_buffer_copy(resp)))
        except Full:
            logger.error('Worker output queue full.')

    def run(self):
        log.thread_local.name = self.name
        logger.info(f'Thread start.')

        # Outer loop
        while not self._stop_event.is_set():
            try:
                self._db_engine.device.init_start_connection(self._device.id)
                logger.info('Device connecting.')
                if self._connect():
                    self._db_engine.device.set_connected(self._device.id)
                    logger.info('Device connected.')

                    # Inner loop
                    self._service_cmds()
            except Exception as err:
                logger.exception(err)

            # Cleanup
            self._disconnect()
            logger.info('Device disconnected.')
            self._db_engine.device.clear_connected(self._device.id)

            # Reconnect
            if not self._stop_event.is_set():
                self._db_engine.device.set_error(self._device.id)
                if not self._stop_event.wait(self._RECONNECT_RETRY_DELAY_SECONDS):
                    self._reconnect_attempt += 1
                    if self._do_report_reconnect():
                        logger.info(f'Reconnection attempt {self._reconnect_attempt}')

        logger.info(f'Thread exit.')
