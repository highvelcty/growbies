import logging

from .queue import ServiceQueue, IDQueue
from.cmd.structs import *
from growbies.service.cmd import activate, discovery
from growbies.session import get_session
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)


class Service:
    def __init__(self):
        # This will initiate the execution session. It needs to be called early in the execution
        # flow so that things can be initialized for use, such as logging.
        get_session()

        self._queue = ServiceQueue()

    @staticmethod
    def _connect_all_active():
        get_pool().connect(*(dev.id for dev in discovery.ls() if dev.is_active()))

    def run(self):
        self._connect_all_active()

        done = False
        try:
            while not done:
                for cmd in self._queue.get():
                    logger.info(f'Service cmd "{cmd.cmd}".')
                    if cmd.cmd == Cmd.SERVICE_STOP:
                        done = True
                        break
                    elif cmd.cmd == Cmd.LS:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(discovery.ls())
                    elif cmd.cmd == Cmd.ACTIVATE:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.activate(cmd))
                    elif cmd.cmd == Cmd.DEACTIVATE:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.deactivate(cmd))
                    elif cmd.cmd == Cmd.RECONNECT:
                        resp = activate.deactivate(cmd)
                        if resp:
                            logger.error(resp)
                        resp = activate.activate(cmd)
                        if resp:
                            logger.error(resp)
                    else:
                        logger.error(f'Unknown command {cmd} received.')
        except KeyboardInterrupt:
            self._queue.put(ServiceStopCmd())
            return self.run()

        get_pool().disconnect_all()
        get_pool().join_all()
        return None
