from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
import os
import shlex
import sys
from . import __doc__ as pkg_doc
from . import cfg, db, human_input, monitor, plot, sample, service
from .constants import USERNAME
from .utils.privileges import drop_privileges

CMD = 'cmd'


class SubCmd(StrEnum):
    LS = 'ls'
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'SubCmd') -> str:
        if sub_cmd_ == cls.LS:
            return f'List discovered devices merged with known devices in the DB.'
        elif sub_cmd_ == cls.ACTIVATE:
            return f'Activate a device, making it available for connection.'
        elif sub_cmd_ == cls.DEACTIVATE:
            return ('Deactivate a device. Disconnecting as necessary and making it unavailable '
                    'for connection.')
        else:
            raise ValueError(f'Sub-command "{sub_cmd_}" does not exist')

class Param:
    KEEP_PRIVILEGES = 'keep_privileges'

class ActivateSubCmd(StrEnum):
    SERIALS = 'serials'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'ActivateSubCmd') -> str:
        if sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')

parser = ArgumentParser(description=pkg_doc,
                        formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for pkg in (cfg, db, human_input, monitor, plot, sample, service):
    parser_adder.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)
for sub_cmd in SubCmd:
    parsers[sub_cmd] = parser_adder.add_parser(sub_cmd,
                                               help=SubCmd.get_help_str(sub_cmd))

parser.add_argument(f'--{Param.KEEP_PRIVILEGES}', default=False, action='store_true',
                    help=f'By default, if the program is executed with root privileges, these will '
                         f'be dropped by switching to the "{USERNAME}" user. This is typically '
                         f'only seto to False during package installation work.')

# Activate and Deactivate
for sub_parser in (parsers[SubCmd.ACTIVATE], parsers[SubCmd.DEACTIVATE]):
    sub_parser.add_argument(ActivateSubCmd.SERIALS, nargs='+', type=str,
                            help=ActivateSubCmd.get_help_str(ActivateSubCmd.SERIALS))

ns, args = parser.parse_known_args(sys.argv[1:])

if not getattr(ns, Param.KEEP_PRIVILEGES):
    drop_privileges()
delattr(ns, Param.KEEP_PRIVILEGES)

cmd = getattr(ns, CMD)

# Lazy import
try:
    cmd = SubCmd(cmd)
    from growbies.service.cmd.structs import *
    from growbies.service.queue import IDQueue, ServiceQueue

    def _run_cmd(cmd_: TBaseCmd):
        with ServiceQueue() as cmd_q, IDQueue() as resp_q:
            cmd_.qid = resp_q.qid
            cmd_q.put(cmd_)
            return next(resp_q.get())

    if SubCmd.LS == cmd:
        print(_run_cmd(DeviceLsCmd()))
    elif SubCmd.ACTIVATE == cmd:
        cmd = ActivateCmd(serials=getattr(ns, ActivateSubCmd.SERIALS))
        ret = _run_cmd(cmd)
        if ret is not None:
            sys.stderr.write(f'{ret}\n')
            sys.exit(1)
    elif SubCmd.DEACTIVATE == cmd:
        ret = _run_cmd(DeactivateCmd(serials=getattr(ns, ActivateSubCmd.SERIALS)))
        if ret is not None:
            sys.stderr.write(f'{ret}\n')
            sys.exit(1)
    sys.exit(0)
except ValueError:
    pass

sub_cmd = shlex.split(f'{sys.executable} -m {__package__}.{getattr(ns, CMD)} ') + args
os.execvp(sys.executable, sub_cmd)

