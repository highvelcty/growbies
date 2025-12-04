from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum

from . import calibration, identify, tare
from growbies.cli.common import SUBCMD

__all__ = ['SubCmd', 'make_cli']

class SubCmd(StrEnum):
    CAL = 'cal'
    ID = 'id'
    TARE = 'tare'

    @property
    def description(self):
        desc = f'Description for element {self} has not been implemented.'
        if self == self.CAL:
            desc = f'List/modify/initialize device calibration.'
        elif self == self.ID:
            desc = f'List/modify/initialize device identify information.'
        elif self == self.TARE:
            desc = f'Read, modify or initialize tare.'

        return (f'{self.help}\n'
                f'\n'
                f'{desc}')

    @property
    def help(self):
        if self == self.CAL:
            return f'Get/set calibration information.'
        elif self == self.ID:
            return f'Get/set device identify information.'
        elif self == self.TARE:
            return f'Get/set tare slots.'
        return f'Help for element {self} has not been implemented.'

def make_cli(parser: ArgumentParser):
    parser_adder = parser.add_subparsers(dest=SUBCMD, required=True)

    parsers = dict()
    for subcmd in SubCmd:
        parsers[subcmd] = parser_adder.add_parser(subcmd,
                                                  description=subcmd.description, help=subcmd.help,
                                                  formatter_class=RawDescriptionHelpFormatter)
    calibration.make_cli(parsers[SubCmd.CAL])
    identify.make_cli(parsers[SubCmd.ID])
    tare.make_cli(parsers[SubCmd.TARE])
