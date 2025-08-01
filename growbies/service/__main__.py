from argparse import ArgumentParser, RawTextHelpFormatter
import errno
import logging
import os
import signal
import sys

from . import __doc__ as pkg_doc
from . import Op
from . service import Service
from growbies.utils.filelock import PidFileLock
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

CMD = 'cmd'

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)
for command in Op:
    sub.add_parser(command, help=Op.get_help_str(command), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
cmd = getattr(ns_args, CMD)


if Op.START == cmd:
    path_to_service_lock_file = InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value
    try:
        with PidFileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'w') as lock:
            Service().run()
    except BlockingIOError as err:
        if err.errno == errno.EAGAIN:
            logger.error('Unable to exclusively lock the service main loop file. Most likely, '
                         'another process has it.')
elif Op.STOP == cmd:
    os.kill(PidFileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'r').get_pid(),
            signal.SIGINT)
