from argparse import ArgumentParser, RawTextHelpFormatter
import fcntl
import logging
import sys

from . import __doc__ as pkg_doc
from . import Op, service
from growbies.session import Session
from growbies.utils.filelock import FileLock
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

CMD = 'cmd'

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)
for command in Op:
    sub.add_parser(command, help=Op.get_help_str(command), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
cmd = getattr(ns_args, CMD)

_ = Session()

queue = service.Queue()

if Op.START == cmd:
    path_to_service_lock_file = InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value
    with FileLock(InstallPaths.VAR_LIB_GROWBIES_LOCK_SERVICE.value, 'w') as lock:
        service.main()
elif Op.STOP == cmd:
    queue.put(service.StopCmd())
