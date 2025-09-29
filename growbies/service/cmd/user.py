from argparse import ArgumentParser
from enum import StrEnum
from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.db.engine import get_db_engine
from growbies.db.models import user

logger = logging.getLogger(__name__)

class PositionalParam(StrEnum):
    GET_NAME = 'get_name'

    @property
    def help(self) -> str:
        if self == self.GET_NAME:
            return 'Get a user by name'
        else:
            return ''

class KwParam(StrEnum):
    SET_NAME = 'set_name'
    EMAIL = 'email'
    REMOVE = 'remove'

    @property
    def help(self) -> str:
        if self == self.SET_NAME:
            return 'Rename a user.'
        elif self == self.EMAIL:
            return 'Set email.'
        elif self == self.REMOVE:
            return 'Remove a user.'
        else:
            return ''

def make_cli(parser: ArgumentParser):
    parser.add_argument(
        PositionalParam.GET_NAME,
        nargs='?',  # zero or one time
        default=None,  # default if not provided
        help=PositionalParam.GET_NAME.help
    )

    for param in (KwParam.SET_NAME, KwParam.EMAIL):
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

def execute(cmd: ServiceCmd) -> Optional[user.Users]:
    engine = get_db_engine()
    get_name = cmd.kw.pop(PositionalParam.GET_NAME)
    email = cmd.kw.pop(KwParam.EMAIL)
    remove = cmd.kw.pop(KwParam.REMOVE)
    set_name = cmd.kw.pop(KwParam.SET_NAME)

    if remove:
        if get_name is None:
            raise ServiceCmdError(f'Must provide {PositionalParam.GET_NAME} to remove a user.')
        if not engine.user.remove(get_name):
            raise ServiceCmdError(f'Failed to remove user "{get_name}"')
        return None

    user_ = engine.user.get(get_name)

    if email is None and set_name is None:
        if user_ is None:
            return engine.user.list()
        else:
            return user.Users([user_])
    else:
        if user_ is None:
            if set_name is None:
                raise ServiceCmdError(f'Must provide --{KwParam.SET_NAME} to create a new user.')
            user_ = user.User(name=set_name, email=email)
        else:
            if set_name:
                user_.name = set_name
            if email:
                user_.email = email
        engine.user.upsert(user_)
        return None
