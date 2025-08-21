import logging
import os
import time
from queue import Queue
from select import select
from threading import Thread
from typing import Optional

from serial.serialutil import SerialException

from growbies.db.engine import get_db_engine
from growbies.intf import Intf
from growbies.intf.cmd import BaseCmd, TBaseCmd
from growbies.intf.resp import Resp, RespError, RespDataPoint, TBaseResp
from growbies.service.cmd.structs import ReconnectCmd
from growbies.service.queue import ServiceQueue
from growbies.session import log
from growbies.utils.types import DeviceID_t, WorkerID_t

logger = logging.getLogger(__name__)

class PipeCmd:
    STOP = b'stop'
    WAKE = b'wake'

class Worker(Thread):
    _RECONNECT_RETRY_DELAY_SECONDS = 3
    _ASYNC_RESPONSES = (RespDataPoint, RespError)
    _PIPE_READ_BYTES = 1024
    def __init__(self, device_id: DeviceID_t):
        super().__init__()
        self._in_queue = Queue()
        self._out_queue = Queue()
        self._engine = get_db_engine().devices.get_engine(device_id)
        self._device = self._engine.get(device_id)
        self._intf: Optional[Intf] = None
        self._retry_connection_flag = True
        self._rpipe, self._wpipe = os.pipe()
        self._transaction_id = 1

    @property
    def id(self) -> WorkerID_t:
        return self._device.id

    def cmd(self, cmd: TBaseCmd) -> TBaseResp:
        self._in_queue.put(cmd)
        os.write(self._wpipe, PipeCmd.WAKE)
        return self._out_queue.get()

    @property
    def name(self):
        return f'{self._device.serial}'

    def stop(self):
        os.write(self._wpipe, PipeCmd.STOP)

    def _retry_connection(self):
        logger.info(f'Connection retry.')
        time.sleep(self._RECONNECT_RETRY_DELAY_SECONDS)
        cmd = ReconnectCmd(serials=(self._device.serial,))
        with ServiceQueue() as cmd_q:
            cmd_q.put(cmd)

    def _connect(self) -> bool:
        try:
            self._intf = Intf(port=self._device.path)
        except SerialException as err:
            if err.errno == 2:
                logger.error(f'Could not open serial port {self._device.path}.')
                return False
            else:
                logger.exception(err)
                raise err

        self._intf.reset_output_buffer()
        self._intf.reset_input_buffer()
        return True

    def _disconnect(self):
        if self._intf:
            self._intf.close()

    @staticmethod
    def _process_async(resp: RespDataPoint | RespError):
        logger.info(f'Process {resp.type}')
        if resp.type == Resp.ERROR:
            pass
        elif resp.type == Resp.DATAPOINT:
            pass
        else:
            logger.error(f'Invalid response type received: {resp.type}.')

    def _service_cmds(self):
        while True:
            # Wait for either serial or rpipe to be readable
            rlist, _, _ = select([self._intf.fileno(), self._rpipe], [], [])
            if self._rpipe in rlist:
                # Pipe wake and drain
                pipe_cmd = os.read(self._rpipe, self._PIPE_READ_BYTES)
                if pipe_cmd == PipeCmd.STOP:
                    self._retry_connection_flag = False
                    break
                elif pipe_cmd == PipeCmd.WAKE:
                    cmd: BaseCmd = self._in_queue.get()
                    logger.info(f'Sending {cmd.type} command to device.')
                    self._transaction_id += 1
                    cmd.id = self._transaction_id
                    self._intf.send_cmd(cmd)
                    continue

            resp = self._intf.recv_resp()
            if resp is not None:
                if resp.id == self._transaction_id:
                    self._transaction_id -= 1
                    logger.info(f'Received {resp.type} response from device, sending to client.')
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
            if self._retry_connection_flag:
                self._retry_connection()
            logger.info(f'Thread exit.')
