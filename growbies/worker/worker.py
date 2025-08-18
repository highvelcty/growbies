import logging
from queue import Queue
from threading import Thread
from typing import cast, Optional

from growbies.service.cmd.structs import BaseCmd, TBaseCmd
from growbies.service.resp.structs import TBaseResp
from growbies.utils.types import DeviceID_t, WorkerID_t

logger = logging.getLogger(__name__)

class Worker(Thread):
    def __init__(self, device_id: DeviceID_t):
        super().__init__()
        self._id: WorkerID_t = cast(WorkerID_t, device_id)
        self._cmd_queue = Queue()
        self._resp_queue = Queue()

    def cmd(self, cmd: TBaseCmd) -> TBaseResp:
        self._cmd_queue.put(cmd)
        return self._resp_queue.get()

    @property
    def id(self) -> WorkerID_t:
        return self._id

    def stop(self):
        self._cmd_queue.put(None)

    def run(self):
        logger.info(f'Worker ID {self._id} starting.')
        while True:
            cmd: Optional[BaseCmd] = self._cmd_queue.get()
            if cmd is None:
                break

        logger.info(f'Worker ID {self.id} exiting.')
