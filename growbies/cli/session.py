from argparse import ArgumentParser
from enum import StrEnum

class Param(StrEnum):
    SESSION_NAME = 'session_name'
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

class Entity(StrEnum):
    DEVICE = 'device'
    PROJECT = 'project'
    TAG = 'tag'
    USER = 'user'

def make_cli(parser: ArgumentParser):
    """
    Configures the session CLI commands.
    SESSION_NAME is now a positional parameter for each action.
    """

    subparsers = parser.add_subparsers(dest=Param.ACTION, required=False)

    # LS
    ls_parser = subparsers.add_parser(Action.LS, help='Show session details.')
    ls_parser.add_argument(Param.SESSION_NAME, nargs='?', default=None,
                           help='Session to operate on.')

    # Activate / Deactivate
    for act in (Action.ACTIVATE, Action.DEACTIVATE):
        act_parser = subparsers.add_parser(act, help=f'{act.capitalize()} session.')
        act_parser.add_argument(Param.SESSION_NAME, nargs='?', default=None,
                                help='Session to operat e on.')

    # Add / Remove
    for cmd in (Action.ADD, Action.RM):
        cmd_parser = subparsers.add_parser(cmd, help=f'{cmd.capitalize()} entities.')
        cmd_parser.add_argument(Param.SESSION_NAME, nargs='?', default=None,
                                help='Session to operate on.')
        for entity in Entity:
            cmd_parser.add_argument(
                f'--{entity}', nargs='+', default=tuple(),
                help=f'Name(s) of {entity}(s) to {cmd}.'
            )
        if cmd == Action.RM:
            cmd_parser.add_argument(
                f'--{RmParam.SELF}', action='store_true', help='Remove the session itself.'
            )

    # New / Mod
    for cmd in (Action.NEW, Action.MOD):
        cmd_parser = subparsers.add_parser(cmd, help=f'{cmd} session.')
        cmd_parser.add_argument(Param.SESSION_NAME, nargs='?', default=None,
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
