from argparse import ArgumentParser
from enum import StrEnum

from growbies.db.models.session import Entity
from growbies.cli.common import Param as commonParam

class Param(StrEnum):
    ACTION = 'action'

class ModNewParam(StrEnum):
    DESCRIPTION = 'description'
    META = 'meta'
    NOTES = 'notes'

class ModParam(StrEnum):
    NEW_NAME = 'new_name'

class RmParam(StrEnum):
    SELF = 'self'

class Action(StrEnum):
    ACTIVATE = 'activate'
    ADD = 'add'
    DEACTIVATE = 'deactivate'
    LS = 'ls'
    MOD = 'mod'
    NEW = 'new'
    RM = 'rm'

    @property
    def help(self) -> str:
        if self == self.ACTIVATE:
            return ('Activate a session. The start time will be set on transition. Clear the end '
                    'time.')
        elif self == self.ADD:
            return 'Add/associate an entity with a session.'
        elif self == self.DEACTIVATE:
            return 'Deactivate a session. Update/set the end time.'
        elif self == self.LS:
            return 'List the details of a session.'
        elif self == self.MOD:
            return 'Modify a session.'
        elif self == self.NEW:
            return 'Create a new session.'
        elif self == self.RM:
            return (f'Remove an entity. Set the --{RmParam.SELF} flag to remove the session '
                    f'permanently.')
        else:
            return ''

def make_cli(parser: ArgumentParser):
    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False)

    # LS
    ls_parser = subparsers.add_parser(Action.LS, help='List session details.')
    ls_parser.add_argument(commonParam.FUZZY_ID, nargs='?', default=None,
                           help='Session to operate on.')

    # Activate / Deactivate
    for act in (Action.ACTIVATE, Action.DEACTIVATE):
        act_parser = subparsers.add_parser(act, help=f'{act.capitalize()} session.')
        act_parser.add_argument(commonParam.FUZZY_ID, nargs='?', default=None,
                                help='Session to operate on.')

    # Add / Remove
    for cmd in (Action.ADD, Action.RM):
        cmd_parser = subparsers.add_parser(cmd, help=cmd.help)
        cmd_parser.add_argument(commonParam.FUZZY_ID, nargs='?', default=None,
                                help='Session to operate on.')
        for entity in (Entity.DEVICE, Entity.PROJECT, Entity.TAG, Entity.USER):
            cmd_parser.add_argument(
                f'--{entity}', nargs='+', default=tuple(),
                help=f'Name(s) of {entity}(s) to add/remove.'
            )
        if cmd == Action.RM:
            cmd_parser.add_argument(
                f'--{RmParam.SELF}', action='store_true', help='Remove the session itself.'
            )

    # New / Mod
    for cmd in (Action.NEW, Action.MOD):
        cmd_parser = subparsers.add_parser(cmd, help=cmd.help)
        cmd_parser.add_argument(commonParam.FUZZY_ID, nargs='?', default=None,
                                help='Session to operate on.')
        cmd_parser.add_argument(f'--{ModNewParam.DESCRIPTION}', type=str,
                                help='Session description.')
        cmd_parser.add_argument(f'--{ModNewParam.META}', type=str,
                                help='Session metadata as JSON string.')
        cmd_parser.add_argument(f'--{ModNewParam.NOTES}', type=str,
                                help='Session notes.')
        if cmd == Action.MOD:
            cmd_parser.add_argument(f'--{ModParam.NEW_NAME}', type=str,
                                    help='The new name for the session.')
