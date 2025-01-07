from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path
import sys

from .exec import execute, monitor, plot
from .session import Session

CMD = 'cmd'

class Level1Cmd(StrEnum):
    EXECUTE = 'execute'
    MONITOR = 'monitor'
    PLOT = 'plot'

class MonitorParam(StrEnum):
    PATH = 'path'
    TAG = 'tag'


def main():
    parser = ArgumentParser(description="Precision farming CLI.")
    sub = parser.add_subparsers(dest=CMD, metavar=CMD)

    help_str = 'Monitor a sensor.'
    sub_sub = sub.add_parser(Level1Cmd.MONITOR, description=help_str, help=help_str)
    sub_sub.add_argument(f'--{MonitorParam.TAG}', action='append', help='Session tags')
    sub_sub.add_argument(f'--{MonitorParam.PATH}',
                         help='Path to session output to begin or resume.')

    help_str = ('Loop execute commands. A prompt will be given for each command. The return of '
                'each command will be output to standard output.')
    sub.add_parser(Level1Cmd.EXECUTE, description=help_str, help=help_str)

    help_str = 'Plot data.'
    sub.add_parser(Level1Cmd.PLOT, description=help_str, help=help_str)

    ns_args = parser.parse_args(sys.argv[1:])

    cmd = getattr(ns_args, CMD)

    if cmd == Level1Cmd.MONITOR:
        tags = getattr(ns_args, MonitorParam.TAG)
        path = getattr(ns_args, MonitorParam.PATH)

        if path is None:
            if tags is None:
                path_or_tags = []
            else:
                path_or_tags = tags
        else:
            path_or_tags = Path(path)
        sess = Session(path_or_tags)
        monitor.main(sess)
    elif cmd == Level1Cmd.EXECUTE:
        _ = Session()
        execute.main()
    elif cmd == Level1Cmd.PLOT:
        _ = Session()
        plot.main()
    elif cmd is None:
        # noinspection PyTypeChecker
        parser.error(f'A command must be given {[cmd.value for cmd in Level1Cmd]}.')
