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
    EXECUTE = Paths.PRECISION_FARMING_EXEC.value.name
    MONITOR = Paths.PRECISION_FARMING_MONITOR.value.name
    PLOT = Paths.PRECISION_FARMING_PLOT.value.name

def main():
    parser = ArgumentParser(description=pkg_doc,
                            formatter_class=RawTextHelpFormatter)
    sub = parser.add_subparsers(dest=CMD, metavar=CMD)
    _ = sub.add_parser(Level1Cmd.MONITOR, help=monitor.__doc__, add_help=False)
    sub.add_parser(Level1Cmd.EXECUTE, help=exec.__doc__)

    _ = sub.add_parser(Level1Cmd.PLOT, help=plot.__doc__)

    ns, args = parser.parse_known_args(sys.argv[1:])
    cmd = getattr(ns, CMD)

    if cmd in Level1Cmd:
        sub_cmd = shlex.split(
            f'{sys.executable} -m '
            f'{Paths.PRECISION_FARMING.value.name}.{cmd} '
        ) + sys.argv[2:]
        os.execvp(sys.executable, sub_cmd)
    else:
        # noinspection PyTypeChecker
        parser.error(f'A command must be given {[cmd.value for cmd in Level1Cmd]}.')



