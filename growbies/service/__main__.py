from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import errno
import logging
import os
import signal
import sys

from . import __doc__ as pkg_doc
from . service import Service
from growbies.constants import APPNAME
from growbies.utils.filelock import PidFileLock
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

CMD = 'cmd'

class SubCmd(StrEnum):
    START = 'start'
    STOP = 'stop'

    @classmethod
    def get_help_str(cls, op: 'Op') -> str:
        if op == cls.START:
            return f'Start the {APPNAME} service.'
        elif op == cls.STOP:
            return f'Stop the {APPNAME} service.'
        else:
            raise ValueError(f'Service command operation "{op}" does not exist')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)
for command in SubCmd:
    sub.add_parser(command, help=SubCmd.get_help_str(command), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
cmd = getattr(ns_args, CMD)


if SubCmd.START == cmd:
    path_to_service_lock_file = InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value
    try:
        with PidFileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'w') as lock:
            Service().run()
    except BlockingIOError as err:
        if err.errno == errno.EAGAIN:
            logger.error('Unable to exclusively lock the service main loop file. Most likely, '
                         'another process has it.')
elif SubCmd.STOP == cmd:
    os.kill(PidFileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'r').get_pid(),
            signal.SIGINT)
