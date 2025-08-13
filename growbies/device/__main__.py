from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import logging
import os
import sys

from . import __doc__ as pkg_doc
from growbies.service import PidQueue, ServiceQueue
from growbies.models.service import DeviceLsCmd

logger = logging.getLogger(__name__)

SUBCMD = 'subcmd'

class SubCmd(StrEnum):
    LS = 'ls'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'SubCmd') -> str:
        if sub_cmd_ == cls.LS:
            return f'List (discover) devices.'
        else:
            raise ValueError(f'Sub-command "{sub_cmd_}" does not exist')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=SUBCMD, required=True)
for sub_cmd in SubCmd:
    sub.add_parser(sub_cmd, help=SubCmd.get_help_str(sub_cmd), add_help=False)

ns_args = parser.parse_args(sys.argv[1:])
sub_cmd = getattr(ns_args, SUBCMD)

if SubCmd.LS == sub_cmd:
    pid = os.getpid()
    with ServiceQueue() as cmd_q, PidQueue() as resp_q:
        cmd_q.put(DeviceLsCmd())
        print(next(resp_q.get()))
