import logging

from .cmd.ls import (get_device_monitor_singleton, make_device_monitor_singleton,
                     stop_device_monitor_singleton)
from .common import ServiceCmd, ServiceOp, ServiceCmdError
from .service_queue import ServiceQueue, IDQueue
from growbies.protocol.resp import DeviceError
from growbies.service.cmd import cal, device, project, read, session, tag, thermal, user
from growbies.service.cmd import nvm
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

        # Construction order matters. The callback requires the service queue.
        make_device_monitor_singleton([self.service_connections_callback])

    def service_connections_callback(self):
        self._queue.put(ServiceCmd(op=ServiceOp.SERVICE_CONNECTIONS, kw={}))

    def run(self):
        logger.info('Service start.')

        done = False
        try:
            while not done:
                for cmd in self._queue.get_w_timeout(QUEUE_GET_TIMEOUT_SEC):
                    logger.info(f'Servicing {cmd.op} command.')
                    with IDQueue(cmd.qid) as resp_q:
                        try:
                            if cmd.op == ServiceOp.CAL:
                                resp = cal.execute(cmd)
                            elif cmd.op == ServiceOp.DEVICE:
                                resp = device.execute(cmd, self.service_connections_callback)
                            elif cmd.op == ServiceOp.NVM:
                                resp = nvm.execute(cmd)
                            elif cmd.op == ServiceOp.PROJECT:
                                resp = project.execute(cmd)
                            elif cmd.op == ServiceOp.READ:
                                resp = read.execute(cmd)
                            elif cmd.op == ServiceOp.SESSION:
                                resp = session.execute(cmd)
                            elif cmd.op == ServiceOp.TAG:
                                resp = tag.execute(cmd)
                            elif cmd.op == ServiceOp.THERMAL:
                                resp = thermal.execute(cmd)
                            elif cmd.op == ServiceOp.USER:
                                resp = user.execute(cmd)
                            elif cmd.op == ServiceOp.SERVICE_CONNECTIONS:
                                resp = get_pool().synchronize(get_device_monitor_singleton())
                            else:
                                resp = ServiceCmdError(f'Unknown command "{cmd.op}" received.')
                        except (DeviceError, ServiceCmdError) as err:
                            logger.error(err)
                            resp = err

                        if isinstance(resp, Exception) or resp is None:
                            resp_q.put(resp)
                        else:
                            resp_q.put(str(resp))

        except KeyboardInterrupt:
            pass
        finally:
            stop_device_monitor_singleton()
            get_pool().disconnect_all()
            logger.info('Service exit.')
