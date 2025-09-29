import errno
import logging
from .service import Service
from growbies.utils.filelock import PidFileLock
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)
try:
    with PidFileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'w') as lock:
        Service().run()
except BlockingIOError as err:
    if err.errno == errno.EAGAIN:
        logger.error('Unable to exclusively lock the service main loop file. Most likely, '
                     'another process has it.')
