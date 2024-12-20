from argparse import ArgumentParser
from enum import StrEnum
import logging
import sys

from .exec import execute, monitor
from .utils import log
from .utils.paths import Paths

CMD = 'cmd'

class Level1Cmd(StrEnum):
    EXECUTE = 'execute'
    MONITOR = 'monitor'


def main():
    log.start(Paths.LOG_FILE.value, logging.INFO, logging.INFO)

    parser = ArgumentParser(description="Precision farming CLI.")
    sub = parser.add_subparsers(dest=CMD, metavar=CMD)

    help_str = 'Monitor a sensor.'
    sub.add_parser(Level1Cmd.MONITOR, description=help_str, help=help_str)

    help_str = ('Loop execute commands. A prompt will be given for each command. The return of '
                'each command will be output to standard output.')
    sub.add_parser(Level1Cmd.EXECUTE, description=help_str, help=help_str)

    ns_args = parser.parse_args(sys.argv[1:])

    cmd = getattr(ns_args, CMD)

    if cmd == Level1Cmd.MONITOR:
        monitor.main()
    elif cmd == Level1Cmd.EXECUTE:
        execute.main()
    elif cmd is None:
        # noinspection PyTypeChecker
        parser.error(f'A command must be given {[cmd.value for cmd in Level1Cmd]}.')
