from argparse import ArgumentParser, RawDescriptionHelpFormatter
import os
import shlex
import sys
from . import __doc__ as pkg_doc
from . import cfg, db, device, exec, human_input, monitor, plot, sample, service
from .constants import USERNAME
from .utils.privileges import drop_privileges

CMD = 'cmd'

class Param:
    KEEP_PRIVILEGES = 'keep_privileges'

parser = ArgumentParser(description=pkg_doc,
                        formatter_class=RawDescriptionHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)

for pkg in (cfg, db, device, exec, human_input, monitor, plot, sample, service):
    sub.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)

parser.add_argument(f'--{Param.KEEP_PRIVILEGES}', default=False, action='store_true',
                    help=f'By default, if the program is executed with root privileges, these will '
                         f'be dropped by switching to the "{USERNAME}" user. This is typically '
                         f'only seto to False during package installation work.')

ns, args = parser.parse_known_args(sys.argv[1:])

if not getattr(ns, Param.KEEP_PRIVILEGES):
    drop_privileges()
delattr(ns, Param.KEEP_PRIVILEGES)

sub_cmd = shlex.split(f'{sys.executable} -m {__package__}.{getattr(ns, CMD)} ') + args

os.execvp(sys.executable, sub_cmd)

