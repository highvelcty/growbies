import logging
import os
import time
from queue import Queue
from threading import Thread
from typing import Optional

from serial.serialutil import SerialException

from growbies.db.engine import get_db_engine
from growbies.intf import Intf
from growbies.service.cmd.structs import BaseCmd, TBaseCmd, ReconnectCmd
from growbies.service.resp.structs import TBaseResp
from growbies.service.queue import IDQueue, ServiceQueue
from growbies.utils.types import DeviceID_t, WorkerID_t

logger = logging.getLogger(__name__)

class ContextAdapter(logging.LoggerAdapter):
    class ExtraKey:
        WORKER_NAME = 'worker_name'

    def process(self, msg, kwargs):
        return f"{self.extra[ContextAdapter.ExtraKey.WORKER_NAME]}: {msg}", kwargs

class Worker(Thread):
    _RECONNECT_RETRY_DELAY_SECONDS = 3
    def __init__(self, device_id: DeviceID_t):
        super().__init__()
        self._cmd_queue = Queue()
        self._resp_queue = Queue()
        self._engine = get_db_engine().devices.get_engine(device_id)
        self._device = self._engine.get(device_id)
        self._retry_connection = True

        self.logger = ContextAdapter(logger,
                                     {ContextAdapter.ExtraKey.WORKER_NAME: f'{self.name}'})

    @property
    def id(self) -> WorkerID_t:
        return self._device.id

    def cmd(self, cmd: TBaseCmd) -> TBaseResp:
        self._cmd_queue.put(cmd)
        return self._resp_queue.get()

    @property
    def name(self):
        return f'worker {self.id}'

    def stop(self):
        self._cmd_queue.put(None)

    def _do_retry_connection(self):
        self.logger.info(f'Connection retry.')
        time.sleep(self._RECONNECT_RETRY_DELAY_SECONDS)
        cmd = ReconnectCmd(serials=(self._device.serial,))
        with ServiceQueue() as cmd_q:
            cmd_q.put(cmd)

    def _connect(self) -> bool:
        try:
            intf = Intf(port=self._device.path)
        except SerialException as err:
            if err.errno == 2:
                self.logger.error(f'Could not open serial port {self._device.path}.')
                return False
            else:
                self.logger.exception(err)
                raise err
        return True

    def _service_cmds(self):
        while True:
            cmd: Optional[BaseCmd] = self._cmd_queue.get()
            if cmd is None:
                self._retry_connection = False
                break

    def run(self):
        try:
            self.logger.info(f'Starting.')
            self._engine.init_start_connection()
            if self._connect():
                self._engine.set_connected()
                self._service_cmds()
        except Exception as err:
            self.logger.error(f'Exception.')
            self.logger.exception(err)
            self._engine.set_error()
        finally:
            if self._retry_connection:
                self._do_retry_connection()
            self.logger.info(f'Exiting.')
