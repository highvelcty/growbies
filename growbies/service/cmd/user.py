from typing import Optional
import logging

from ..common import ServiceCmd
from growbies.cli.common import Param
from growbies.cli.user import Action, ModParam
from growbies.db.engine import get_db_engine
from growbies.db.models import user

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[user.Users]:
    engine = get_db_engine()

    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    action = cmd.kw.pop(Param.ACTION)

    if action in (None, Action.LS):
        if fuzzy_id is None:
            return engine.user.list()
        else:
            return engine.user.get(fuzzy_id)
    elif action == Action.MOD:
        model = engine.user.get(fuzzy_id)
        model.name = cmd.kw.pop(ModParam.NAME, model.name)
        model.email = cmd.kw.pop(ModParam.EMAIL, model.email)
        engine.user.upsert(model)
    elif action == Action.NEW:
        model = user.User(name=cmd.kw.pop(ModParam.NAME), email=cmd.kw.pop(ModParam.EMAIL, ''))
        engine.user.upsert(model)
    elif action == Action.RM:
        engine.user.remove(fuzzy_id)
    return None
