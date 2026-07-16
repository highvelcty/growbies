from argparse import ArgumentParser, SUPPRESS
from enum import StrEnum

from growbies.cli.common import Param

__all__ = ['make_cli', 'Action', 'ModParam']

class Action(StrEnum):
    CFG = 'cfg'

    @property
    def help(self) -> str:
        if self == self.CFG:
            return 'Get the thermal device configuration.'
        else:
            return ''

class ModParam(StrEnum):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    SET_POINT = 'set_point'

    @property
    def help(self) -> str:
        if self == self.ACTIVATE:
            return 'Activate the thermal device; turn it on.'
        elif self == self.DEACTIVATE:
            return 'Deactivate the thermal device; turn it off'
        elif self == self.SET_POINT:
            return 'The temperature set point, in Celsius, of the thermal device.'
        return ''


# def make_cli(parser: ArgumentParser):
#     subparsers = parser.add_subparsers(dest=Param.ACTION, required=False, help=Param.ACTION.help,)
#     for act in Action:
#         act_parser = subparsers.add_parser(act, help=act.help)
#         act_parser.add_argument(Param.FUZZY_ID, nargs='?', default=None, help=Param.FUZZY_ID.help)
#         if act == Action.CFG:
#             act_parser.add_argument(ModParam.ACTIVATE, help=ModParam.ACTIVATE.help)
#             act_parser.add_argument(ModParam.DEACTIVATE, help=ModParam.DEACTIVATE.help)
#             act_parser.add_argument(f'--{ModParam.SET_POINT}', type=str,
#                                     help=ModParam.SET_POINT.help, default=SUPPRESS)
#

def make_cli(parser: ArgumentParser):
    subparsers = parser.add_subparsers(
        dest=Param.ACTION,
        required=False,
        help=Param.ACTION.help,
    )

    for act in Action:
        act_parser = subparsers.add_parser(act, help=act.help)
        act_parser.add_argument(
            Param.FUZZY_ID,
            nargs='?',
            default=None,
            help=Param.FUZZY_ID.help,
        )

        if act == Action.CFG:
            activate_group = act_parser.add_mutually_exclusive_group()

            activate_group.add_argument(
                f'--{ModParam.ACTIVATE}',
                dest=ModParam.ACTIVATE,
                action='store_true',
                default=SUPPRESS,
                help=f'{ModParam.ACTIVATE.help} (mutually exclusive with --{ModParam.DEACTIVATE}).',
            )

            activate_group.add_argument(
                f'--{ModParam.DEACTIVATE}',
                dest=ModParam.ACTIVATE,
                action='store_false',
                default=SUPPRESS,
                help=f'{ModParam.DEACTIVATE.help} (mutually exclusive with --{ModParam.ACTIVATE}).',
            )

            act_parser.add_argument(
                f'--{ModParam.SET_POINT}',
                type=str,
                help=ModParam.SET_POINT.help,
                default=SUPPRESS,
            )