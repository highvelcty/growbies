import logging

from .common import ServiceCmd, ServiceCmdError
from .queue import ServiceQueue, IDQueue
from growbies.device.resp import DeviceError
from growbies.service.cmd import activate, loopback, ls, identify
from growbies.session import get_session
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

QUEUE_GET_TIMEOUT_SEC = 10

class Service:
    def __init__(self):
        # This will initiate the execution session. It needs to be called early in the execution
        # flow so that things can be initialized for use, such as logging.
        self._session =  get_session()

        self._queue = ServiceQueue()

    @staticmethod
    def _connect_all_active():
        get_pool().connect(*(dev.id for dev in ls.ls() if dev.is_active()))

    def run(self):
        logger.info('Service start.')
        self._connect_all_active()

        done = False
        try:
            while not done:
                for cmd in self._queue.get_w_timeout(QUEUE_GET_TIMEOUT_SEC):
                    logger.info(f'Servicing {cmd.cmd} command.')
                    with IDQueue(cmd.qid) as resp_q:
                        try:
                            if cmd.cmd == ServiceCmd.ACTIVATE:
                                resp_q.put(activate.activate(cmd))
                            elif cmd.cmd == ServiceCmd.DEACTIVATE:
                                resp_q.put(activate.deactivate(cmd))
                            elif cmd.cmd == ServiceCmd.ID:
                                resp_q.put(identify.get_or_set(cmd))
                            elif cmd.cmd == ServiceCmd.LOOPBACK:
                                resp_q.put(loopback.loopback(cmd))
                            elif cmd.cmd == ServiceCmd.LS:
                                resp_q.put(ls.ls())
                            else:
                                raise ServiceCmdError(f'Unknown command {cmd.cmd} received.')
                        except DeviceError as err:
                            resp_q.put(err)
                        except ServiceCmdError as err:
                            resp_q.put(err)
        except KeyboardInterrupt:
            pass
        get_pool().disconnect_all()
        get_pool().join_all()
        logger.info('Service exit.')
