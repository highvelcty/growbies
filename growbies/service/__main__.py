from argparse import ArgumentParser, RawTextHelpFormatter
import fcntl
import logging
import sys

from . import __doc__ as pkg_doc
from . import Cmd, service
from growbies.session import Session
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

CMD = 'cmd'

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)
for command in Cmd:
    sub.add_parser(command, help=Cmd.get_help_str(command), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
cmd = getattr(ns_args, CMD)

_ = Session()

queue = service.Queue()

if Cmd.START == cmd:
    path_to_service_lock_file = InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value
    with open(path_to_service_lock_file, 'w') as service_lock_file:
        try:
            with fcntl.flock(service_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB):
                service.main()
        except BlockingIOError as err:
            logger.exception(f'Unable to obtain exclusive lock file at '
                             f'"{path_to_service_lock_file}"')
elif Cmd.STOP == cmd:
    queue.put(service.StopCmd())
