from typing import Optional
import logging

from ..common import ServiceCmd
from growbies.cli.session import Action, Entity, Param, ModParam, ModNewParam, RmParam
from growbies.db.models.session import Session, Sessions
from growbies.db.engine import get_db_engine

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[Session | Sessions]:
    engine = get_db_engine()

    logger.error(f'emey incoming to session command:\n    {cmd.kw}')

    session_name = cmd.kw.pop(Param.SESSION_NAME, None)
    action = cmd.kw.pop(Param.ACTION)

    sess = None
    if  action and action != Action.NEW:
        sess = engine.session.get(session_name)

    if action in (Action.ACTIVATE, Action.DEACTIVATE):
        if action == Action.ACTIVATE:
            sess.active = True
        else:
            sess.active = False
    elif action in (Action.ADD, Action.RM):
        remove_self = cmd.kw.pop(RmParam.SELF, None)
        if remove_self:
            engine.session.remove(sess.name)
        else:
            engine.session.add(action, Entity.DEVICE, *cmd.kw.pop(Entity.DEVICE, ()))
            engine.session.add(action, Entity.PROJECT, *cmd.kw.pop(Entity.PROJECT, ()))
            engine.session.add(action, Entity.TAG, *cmd.kw.pop(Entity.TAG, ()))
            engine.session.add(action, Entity.USER, *cmd.kw.pop(Entity.USER, ()))
    elif action in (Action.MOD, Action.NEW):
        description = cmd.kw.pop(ModNewParam.DESCRIPTION)
        meta = cmd.kw.pop(ModNewParam.META)
        notes = cmd.kw.pop(ModNewParam.NOTES)

        if action == Action.NEW:
            sess = Session(name=session_name, description=description, meta=meta, notes=notes)
        elif action == Action.MOD:
            new_name = cmd.kw.pop(ModParam.NEW_NAME)
            sess.name = new_name if new_name is not None else None
            sess.description = description if description is not None else None
            sess.meta = meta if meta is not None else None
            sess.notes = notes if notes is not None else None
        engine.session.upsert(sess)
        return None
    elif action == Action.LS:
        return engine.session.get(session_name)
    else:
        logger.error(f'emey ls that')
        return engine.session.ls()
    return None
