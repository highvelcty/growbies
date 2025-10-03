from argparse import ArgumentParser
from enum import StrEnum

from .common import Param

class Action(StrEnum):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    LS = 'ls'
    MOD = 'mod'
    READ = 'read'

    @property
    def help(self) -> str:
        if self == self.ACTIVATE:
            return ('Activate a device. The start time will be set on transition. Clear the end '
                    'time.')
        elif self == self.DEACTIVATE:
            return 'Deactivate a device. Update/set the end time.'
        elif self == self.LS:
            return 'List the details of a device.'
        elif self == self.MOD:
            return 'Modify a device.'
        elif self == self.READ:
            return 'Read data from a device'
        else:
            return ''

class ModParam(StrEnum):
    NEW_NAME = 'new_name'

    @property
    def help(self) -> str:
        if self == self.NEW_NAME:
            return 'The new name to set for the device.'
        else:
            return ''

class ReadParam(StrEnum):
    TIMES = 'times'
    RAW = 'raw'

    @property
    def help(self) -> str:
        if self == self.TIMES:
            return 'How many times, or samples, to read per datapoint.'
        elif self == self.RAW:
            return 'Read raw values. Do not apply calculations, corrections or calibrations.'
        return ''

def make_cli(parser: ArgumentParser):
    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False, help=Param.ACTION.help,)
    for act in (Action.ACTIVATE, Action.DEACTIVATE, Action.LS, Action.MOD, Action.READ):
        act_parser = subparsers.add_parser(act, help=act.help)
        act_parser.add_argument(Param.FUZZY_ID, nargs='?', default=None,
                                help=Param.FUZZY_ID.help)
        if act == Action.MOD:
            act_parser.add_argument(f'--{ModParam.NEW_NAME}', type=str, help=ModParam.NEW_NAME.help)
        if act == Action.READ:
            for param in ReadParam:
                act_parser.add_argument(f'--{param}', nargs='?', default=None, help=param.help)
