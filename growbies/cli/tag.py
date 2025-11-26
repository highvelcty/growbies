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
            return 'List details of a tag.'
        elif self == self.MOD:
            return 'Modify a tag.'
        elif self == self.NEW:
            return 'Create a new tag.'
        elif self == self.RM:
            return f'Remove a tag.'
        else:
            return ''

class ModParam(StrEnum):
    NAME = 'name'
    DESCRIPTION = 'description'

    @property
    def help(self) -> str:
        if self == self.NAME:
            return 'The new name for a tag.'
        elif self == self.DESCRIPTION:
            return 'A description of the tag.'
        return ''


def make_cli(parser: ArgumentParser):
    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False, help=Param.ACTION.help,)
    for act in Action:
        act_parser = subparsers.add_parser(act, help=act.help)
        if act == Action.NEW:
            act_parser.add_argument(ModParam.NAME, help=ModParam.NAME.help)
            act_parser.add_argument(f'--{ModParam.DESCRIPTION}', type=str,
                                    help=ModParam.DESCRIPTION.help,
                                    default=SUPPRESS)
        else:
            act_parser.add_argument(Param.FUZZY_ID, nargs='?', default=None,
                                    help=Param.FUZZY_ID.help)
        if act == Action.MOD:
            for param in ModParam:
                act_parser.add_argument(f'--{param}', type=str, help=param.help, default=SUPPRESS)
