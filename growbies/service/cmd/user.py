from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.cli.user import KwParam, PositionalParam
from growbies.db.engine import get_db_engine
from growbies.db.models import user

logger = logging.getLogger(__name__)

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
