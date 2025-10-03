from argparse import ArgumentParser, SUPPRESS
from enum import StrEnum

from .common import Param

class Action(StrEnum):
    LS = 'ls'
    MOD = 'mod'
    NEW = 'new'
    RM = 'rm'

    @property
    def help(self) -> str:
        if self == self.LS:
            return 'List details of a user.'
        elif self == self.MOD:
            return 'Modify a user.'
        elif self == self.NEW:
            return 'Create a new user.'
        elif self == self.RM:
            return f'Remove a user.'
        else:
            return ''

class ModParam(StrEnum):
    NAME = 'name'
    EMAIL = 'email'

    @property
    def help(self) -> str:
        if self == self.NAME:
            return 'The new name of the user.'
        elif self == self.EMAIL:
            return 'The email of the user.'
        return ''


def make_cli(parser: ArgumentParser):
    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False, help=Param.ACTION.help,)
    for act in Action:
        act_parser = subparsers.add_parser(act, help=act.help)
        act_parser.add_argument(Param.FUZZY_ID, nargs='?', default=None,
                                help=Param.FUZZY_ID.help)
        if act == Action.NEW:
            act_parser.add_argument(ModParam.NAME, help=ModParam.NAME.help)
            act_parser.add_argument(f'--{ModParam.EMAIL}', type=str, help=ModParam.EMAIL.help,
                                    default=SUPPRESS)
        if act == Action.MOD:
            for param in ModParam:
                act_parser.add_argument(f'--{param}', type=str, help=param.help, default=SUPPRESS)
