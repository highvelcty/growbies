from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
import logging
import sys
from . import __doc__ as pkg_doc
from growbies.service.queue import PidQueue, ServiceQueue
from growbies.models.service import TBaseCmd
from growbies.models.service.cmd import DeviceActivateCmd, DeviceDeactivateCmd, DeviceLsCmd


logger = logging.getLogger(__name__)

SUBCMD = 'subcmd'

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

class ActivateSubCmd(StrEnum):
    SERIALS = 'serials'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'ActivateSubCmd') -> str:
        if sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parser_adder = parser.add_subparsers(dest=SUBCMD, required=True)
parsers = {SUBCMD: parser}
for sub_cmd in SubCmd:
    parsers[sub_cmd] = parser_adder.add_parser(sub_cmd,
                                               help=SubCmd.get_help_str(sub_cmd))

for sub_parser in (parsers[SubCmd.ACTIVATE], parsers[SubCmd.DEACTIVATE]):
    sub_parser.add_argument(
        ActivateSubCmd.SERIALS, nargs='+', type=str,
        help=ActivateSubCmd.get_help_str(ActivateSubCmd.SERIALS))

ns_args = parser.parse_args(sys.argv[1:])
sub_cmd = getattr(ns_args, SUBCMD)

def _run_cmd(cmd: TBaseCmd):
    with ServiceQueue() as cmd_q, PidQueue() as resp_q:
        cmd_q.put(cmd)
        return next(resp_q.get())

if SubCmd.LS == sub_cmd:
    print(_run_cmd(DeviceLsCmd()))
elif SubCmd.ACTIVATE == sub_cmd:
    ret = _run_cmd(DeviceActivateCmd(serials=getattr(ns_args, ActivateSubCmd.SERIALS)))
    if ret is not None:
        print(ret)
        sys.exit(1)
elif SubCmd.DEACTIVATE == sub_cmd:
    ret = _run_cmd(DeviceDeactivateCmd(serials=getattr(ns_args, ActivateSubCmd.SERIALS)))
    if ret is not None:
        print(ret)
        sys.exit(1)
