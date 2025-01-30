from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import os
import shlex
import sys

from . import __doc__ as pkg_doc
from . import exec, monitor, plot
from .utils.paths import Paths


CMD = 'cmd'

class Level1Cmd(StrEnum):
    EXECUTE = Paths.GROWBIES_EXEC.value.name
    MONITOR = Paths.GROWBIES_MONITOR.value.name
    PLOT = Paths.GROWBIES_PLOT.value.name

    @classmethod
    def has_it(cls, cmd: str):
        return cmd in cls._member_names_

parser = ArgumentParser(description=pkg_doc,
                        formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)

for pkg in (exec, monitor, plot):
    sub.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)

ns, args = parser.parse_known_args(sys.argv[1:])
sub_cmd = shlex.split(f'{sys.executable} -m {__package__}.{getattr(ns, CMD)} ') + sys.argv[2:]
os.execvp(sys.executable, sub_cmd)
