import logging

from .queue import ServiceQueue, PidQueue
from growbies.models.service import ServiceStopCmd, Cmd
from growbies.session import Session2

logger = logging.getLogger(__name__)


class Service:
    def __init__(self):
        self._queue = ServiceQueue()
        self._session = Session2()

    def run(self):
        done = False
        try:
            while not done:
                for cmd in self._queue.get():
                    if cmd.cmd == Cmd.SERVICE_STOP:
                        done = True
                        break
                    elif cmd.cmd == Cmd.DEVICE_LS:
                        from growbies.device import ls
                        with PidQueue(cmd.qid) as resp_q:
                            resp_q.put(ls())
                    else:
                        logger.error(f'Unknown command {cmd} received.')
        except KeyboardInterrupt:
            self._queue.put(ServiceStopCmd())
            return self.run()
