import logging

from .common import ServiceOp, ServiceCmdError
from .queue import ServiceQueue, IDQueue
from growbies.device.resp import DeviceError
from growbies.service.cmd import (activate, calibration, deactivate, identify, loopback, ls,
                                  project, read, session, tag, tare, user)
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
        get_pool().connect(*(dev.id for dev in ls.execute() if dev.is_active()))

    def run(self):
        logger.info('Service start.')
        self._connect_all_active()

        done = False
        try:
            while not done:
                for cmd in self._queue.get_w_timeout(QUEUE_GET_TIMEOUT_SEC):
                    logger.info(f'Servicing {cmd.op} command.')
                    with IDQueue(cmd.qid) as resp_q:
                        try:
                            if cmd.op == ServiceOp.ACTIVATE:
                                resp_q.put(activate.execute(cmd))
                            elif cmd.op == ServiceOp.DEACTIVATE:
                                resp_q.put(deactivate.execute(cmd))
                            elif cmd.op == ServiceOp.CAL:
                                resp_q.put(calibration.execute(cmd))
                            elif cmd.op == ServiceOp.ID:
                                resp_q.put(identify.execute(cmd))
                            elif cmd.op == ServiceOp.LOOPBACK:
                                resp_q.put(loopback.execute(cmd))
                            elif cmd.op == ServiceOp.LS:
                                resp_q.put(ls.execute())
                            elif cmd.op == ServiceOp.PROJECT:
                                resp_q.put(project.execute(cmd))
                            elif cmd.op == ServiceOp.READ:
                                resp_q.put(read.execute(cmd))
                            elif cmd.op == ServiceOp.SESSION:
                                resp_q.put(session.execute(cmd))
                            elif cmd.op == ServiceOp.TAG:
                                resp_q.put(tag.execute(cmd))
                            elif cmd.op == ServiceOp.TARE:
                                resp_q.put(tare.execute(cmd))
                            elif cmd.op == ServiceOp.USER:
                                resp_q.put(user.execute(cmd))
                            else:
                                raise ServiceCmdError(f'Unknown command {cmd.op} received.')
                        except DeviceError as err:
                            logger.error(err)
                            resp_q.put(err)
                        except ServiceCmdError as err:
                            logger.error(err)
                            resp_q.put(err)
        except KeyboardInterrupt:
            pass
        get_pool().disconnect_all()
        get_pool().join_all()
        logger.info('Service exit.')
