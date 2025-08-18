import logging

from .queue import ServiceQueue, PidQueue
from.cmd.structs import *
from growbies.service.cmd import activate, discovery
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)


class Service:
    def __init__(self):
        self._queue = ServiceQueue()

    def run(self):
        done = False
        try:
            while not done:
                for cmd in self._queue.get():
                    if cmd.cmd == Cmd.SERVICE_STOP:
                        done = True
                        break
                    elif cmd.cmd == Cmd.DEVICE_LS:
                        with PidQueue(cmd.qid) as resp_q:
                            resp_q.put(discovery.ls())
                    elif cmd.cmd == Cmd.DEVICE_ACTIVATE:
                        with PidQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.activate(cmd))
                    elif cmd.cmd == Cmd.DEVICE_DEACTIVATE:
                        with PidQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.deactivate(cmd))
                    else:
                        logger.error(f'Unknown command {cmd} received.')
        except KeyboardInterrupt:
            self._queue.put(ServiceStopCmd())
            return self.run()

        get_pool().stop_all()
        return None
