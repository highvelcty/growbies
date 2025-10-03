from typing import Optional
import logging

from ..common import ServiceCmd
from growbies.cli.common import Param
from growbies.cli.tag import Action, ModParam
from growbies.db.engine import get_db_engine
from growbies.db.models import tag

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[tag.Tags]:
    engine = get_db_engine().tag

    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    action = cmd.kw.pop(Param.ACTION)

    if action in (None, Action.LS):
        if fuzzy_id is None:
            return engine.list()
        else:
            return engine.get(fuzzy_id)
    elif action == Action.MOD:
        model = engine.get(fuzzy_id)
        model.name = cmd.kw.pop(ModParam.NAME, model.name)
        model.description = cmd.kw.pop(ModParam.DESCRIPTION, model.description)
        engine.upsert(model)
    elif action == Action.NEW:
        model = tag.Tag(name=cmd.kw.pop(ModParam.NAME),
                        description=cmd.kw.pop(ModParam.DESCRIPTION, ''))
        engine.upsert(model)
    elif action == Action.RM:
        engine.remove(fuzzy_id)
    return None
