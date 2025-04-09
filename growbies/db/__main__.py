from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import sys

from . import __doc__ as pkg_doc
from . import init
from growbies.constants import APPNAME

SUBCMD = 'subcmd'

class SubCmd(StrEnum):
    INIT = 'init'

    @classmethod
    def get_help_str(cls, sub_cmd: 'SubCmd') -> str:
        if sub_cmd == cls.INIT:
            return f'Initialize the {APPNAME} local database.'
        else:
            raise ValueError(f'Database sub-command "{sub_cmd}" does not exist')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=SUBCMD, required=True)
for sub_cmd in SubCmd:
    sub.add_parser(sub_cmd, help=SubCmd.get_help_str(sub_cmd), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
sub_cmd = getattr(ns_args, SUBCMD)

if SubCmd.INIT == sub_cmd:
    init.main()
