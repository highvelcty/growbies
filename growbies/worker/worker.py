import logging
import time
from queue import Queue, Empty
from threading import Thread
from typing import Optional

from serial.serialutil import SerialException

from growbies.db.engine import get_db_engine
from growbies.intf import Intf
from growbies.intf.cmd import TDeviceCmd
from growbies.intf.resp import DeviceResp, ErrorDeviceResp, DataPointDeviceResp
from growbies.service.cmd.structs import ReconnectServiceCmd
from growbies.service.queue import ServiceQueue
from growbies.session import log
from growbies.utils.types import DeviceID_t, WorkerID_t

logger = logging.getLogger(__name__)

class PipeCmd:
    STOP = b'stop'
    WAKE = b'wake'

class Worker(Thread):
    _RECONNECT_RETRY_DELAY_SECONDS = 3
    _ASYNC_RESPONSES = (DataPointDeviceResp, ErrorDeviceResp)
    _PIPE_READ_BYTES = 1024
    _DEFAULT_CMD_TIMEOUT_SECONDS = 3
    _RESP_Q_TIMEOUT_SECONDS = 0.1
    def __init__(self, device_id: DeviceID_t):
        super().__init__()
        self._out_queue = Queue()
        self._engine = get_db_engine().devices.get_engine(device_id)
        self._device = self._engine.get(device_id)
        self._intf: Optional[Intf] = None
        self._do_continue = True

    @property
    def id(self) -> WorkerID_t:
        return self._device.id

    def cmd(self, cmd: TDeviceCmd, timeout: Optional[float] = _DEFAULT_CMD_TIMEOUT_SECONDS):
        self._intf.send_cmd(cmd)
        return self._out_queue.get(block=True, timeout=timeout)

    @property
    def name(self):
        return f'{self._device.serial}'

    def stop(self):
        self._do_continue = False
        self.join()

    def _retry_connection(self):
        logger.info(f'Connection retry.')
        time.sleep(self._RECONNECT_RETRY_DELAY_SECONDS)
        cmd = ReconnectServiceCmd(serials=(self._device.serial,))
        with ServiceQueue() as cmd_q:
            cmd_q.put(cmd)

    def _connect(self) -> bool:
        try:
            self._intf = Intf(port=self._device.path, thread_name=f'{self.name}_SLIP')
        except SerialException as err:
            if err.errno == 2:
                logger.error(f'Could not open serial port {self._device.path}.')
                return False
            else:
                logger.exception(err)
                raise err

        self._intf.start()
        return True

    def _disconnect(self):
        if self._intf:
            self._intf.stop()

    @staticmethod
    def _process_async(resp: DataPointDeviceResp | ErrorDeviceResp):
        if resp.type == DeviceResp.ERROR:
            resp: ErrorDeviceResp
            logger.error(f'Received asynchronous error response with error code 0x{resp.error:X}')
        elif resp.type == DeviceResp.DATAPOINT:
            logger.info(f'Received asynchronous {resp.type} response.')
        else:
            logger.error(f'Invalid response type received: {resp.type}.')

    def _service_cmds(self):
        while self._do_continue:
            try:
                resp = self._intf.recv_resp(timeout=self._RESP_Q_TIMEOUT_SECONDS)
            except Empty:
                continue
            if resp is None:
                continue
            if resp.id:
                logger.info(f'Received synchronous {resp.type} response.')
                self._out_queue.put(resp)
            else:
                self._process_async(resp)

    def run(self):
        log.thread_local.name = self.name
        try:
            logger.info(f'Thread start.')
            self._engine.init_start_connection()
            logger.info('Device connecting.')
            if self._connect():
                self._engine.set_connected()
                logger.info('Device connected.')
                self._service_cmds()
        except Exception as err:
            logger.exception(err)
            self._engine.set_error()
        finally:
            self._disconnect()
            logger.info('Device disconnected.')
            self._engine.clear_connected()
            if self._do_continue:
                self._retry_connection()
            logger.info(f'Thread exit.')
