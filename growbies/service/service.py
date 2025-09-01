import logging

from .queue import ServiceQueue, IDQueue
from.cmd.structs import ServiceCmd, ServiceStopServiceCmd
from growbies.service.cmd import activate, discovery, loopback, identify
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
                    if cmd.cmd == ServiceCmd.ACTIVATE:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.activate(cmd))
                    elif cmd.cmd == ServiceCmd.DEACTIVATE:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(activate.deactivate(cmd))
                    elif cmd.cmd == ServiceCmd.ID:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(identify.get(cmd))
                    elif cmd.cmd == ServiceCmd.LOOPBACK:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(loopback.loopback(cmd))
                    elif cmd.cmd == ServiceCmd.LS:
                        with IDQueue(cmd.qid) as resp_q:
                            resp_q.put(discovery.ls())
                    elif cmd.cmd == ServiceCmd.SERVICE_STOP:
                        done = True
                        break
                    else:
                        logger.error(f'Unknown command {cmd} received.')
        except KeyboardInterrupt:
            self._queue.put(ServiceStopServiceCmd())
            return self.run()

        get_pool().disconnect_all()
        get_pool().join_all()
        return None
