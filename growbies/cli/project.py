from argparse import ArgumentParser
from enum import StrEnum

class PositionalParam(StrEnum):
    GET_NAME = 'get_name'

    @property
    def help(self) -> str:
        if self == self.GET_NAME:
            return 'Get a project by name'
        else:
            return ''

class KwParam(StrEnum):
    SET_NAME = 'set_name'
    DESCRIPTION = 'description'
    REMOVE = 'remove'

    @property
    def help(self) -> str:
        if self == self.SET_NAME:
            return 'Rename a project.'
        elif self == self.DESCRIPTION:
            return 'Set project description.'
        elif self == self.REMOVE:
            return 'Remove a project.'
        else:
            return ''

def make_cli(parser: ArgumentParser):
    parser.add_argument(
        PositionalParam.GET_NAME,
        nargs='?',  # zero or one time
        default=None,  # default if not provided
        help=PositionalParam.GET_NAME.help
    )

    for param in (KwParam.SET_NAME, KwParam.DESCRIPTION):
        parser.add_argument(
            f'--{param}',
            type=str,
            default=None,
            help=param.help
        )

    parser.add_argument(
        f'--{KwParam.REMOVE}',
        action='store_true',
        help=KwParam.REMOVE.help
    )
