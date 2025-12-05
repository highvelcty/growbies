from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum

from . import new, resume, stop, mon, ls, evaluate, plot
from growbies.cli.common import SUBCMD

__all__ = ['SubCmd', 'make_cli']

class SubCmd(StrEnum):
    EVAL = 'eval'
    LS = 'ls'
    MON = 'mon'
    NEW = 'new'
    PLOT = 'plot'
    RESUME = 'resume'
    STOP = 'stop'

    @property
    def description(self):
        desc = f'Description for element {self} has not been implemented.'
        if self == self.EVAL:
            desc = f'Evaluate the calibration regression model.'
        elif self == self.LS:
            desc = f'List calibration sessions.'
        elif self == self.MON:
            desc = 'Monitor a calibration session.'
        elif self == self.NEW:
            desc = 'Create a new calibration session.'
        elif self == self.PLOT:
            desc = 'Plot a calibration session.'
        elif self == self.RESUME:
            desc = ('Resume an existing session. An error will be raised if the requested session '
                    'does not exist.')
        elif self == self.STOP:
            desc = 'Stop a session.'
        return desc
    @property
    def help(self):
        if self == self.EVAL:
            return f'Evaluate the calibration regression model.'
        elif self == self.LS:
            return f'List calibration sessions.'
        elif self == self.MON:
            return 'Monitor a calibration session.'
        elif self == self.NEW:
            return 'Create a new calibration session.'
        elif self == self.PLOT:
            return 'Plot a calibration session.'
        elif self == self.RESUME:
            return 'Resume a calibration session'
        elif self == self.STOP:
            return 'Stop a session.'
        return f'Help for element {self} has not been implemented.'

def make_cli(parser: ArgumentParser):
    parser_adder = parser.add_subparsers(dest=SUBCMD, required=True)

    parsers = dict()
    for subcmd in SubCmd:
        parsers[subcmd] = parser_adder.add_parser(subcmd,
                                                  description=subcmd.description, help=subcmd.help,
                                                  formatter_class=RawDescriptionHelpFormatter)
    evaluate.make_cli(parsers[SubCmd.EVAL])
    ls.make_cli(parsers[SubCmd.LS])
    mon.make_cli(parsers[SubCmd.MON])
    new.make_cli(parsers[SubCmd.NEW])
    plot.make_cli(parsers[SubCmd.PLOT])
    resume.make_cli(parsers[SubCmd.RESUME])
    stop.make_cli(parsers[SubCmd.STOP])
