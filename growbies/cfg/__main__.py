from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import sys

from . import __doc__ as pkg_doc
from growbies.constants import APPNAME
from growbies.models.cfg import Cfg

SUBCMD = 'subcmd'

class SubCmd(StrEnum):
    INIT = 'init'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'SubCmd') -> str:
        if sub_cmd_ == cls.INIT:
            return f'Restore the {APPNAME} configuration to default.'
        else:
            raise ValueError(f'Database sub-command "{sub_cmd_}" does not exist')

class InitCmdParam(StrEnum):
    YES = 'yes'

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=SUBCMD, required=False)
for sub_cmd in SubCmd:
    sub_sub = sub.add_parser(sub_cmd, help=SubCmd.get_help_str(sub_cmd), add_help=True)
    if sub_cmd == SubCmd.INIT:
        sub_sub.add_argument(f'-{InitCmdParam.YES[0].lower()}',
                             f'--{InitCmdParam.YES}', action='store_true', default=False)

ns_args = parser.parse_args(sys.argv[1:])
sub_cmd = getattr(ns_args, SUBCMD)

if SubCmd.INIT == sub_cmd:
    if not getattr(ns_args, InitCmdParam.YES):
        while True:
            ans = input(f'Restore {APPNAME} to default? y/n/q: ').lower().strip()
            if ans.startswith('q') or ans.startswith('n'):
                sys.exit()
            elif ans.startswith('y'):
                break
            else:
                print('Unrecognized input.')
    cfg = Cfg()
    cfg.save()
    print(f'Initialized {APPNAME.capitalize()} configuration at: {cfg.PATH}')
else:
    print(Cfg())


