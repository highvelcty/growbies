from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
import logging

from growbies.cli.common import Param

STDIN_LEVEL = logging.INFO + 1
STDOUT_LEVEL = logging.INFO + 2
STDERR_LEVEL = logging.ERROR + 1
logging.addLevelName(STDIN_LEVEL, "STDIN")
logging.addLevelName(STDOUT_LEVEL, "STDOUT")
logging.addLevelName(STDERR_LEVEL, "STDERR")

class Action(StrEnum):
    FINALIZE = 'finalize'

    @property
    def description(self):
        if self == self.FINALIZE:
            return f'Finalize a scale prior to shipping. Bon voyage!'
    @property
    def help(self):
        if self == self.FINALIZE:
            return f'Finalize a scale.'

def make_cli() -> ArgumentParser:
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False, help=Param.ACTION.help,)
    for act in (Action.FINALIZE,):
        act_parser = subparsers.add_parser(act, help=act.help)
        act_parser.add_argument(Param.FUZZY_ID, help=Param.FUZZY_ID.help)
    return parser
