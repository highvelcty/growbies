from typing import Optional
import logging
import cProfile, pstats, io

from ..common import ServiceCmd
from growbies.cli.common import Param as commonParam
from growbies.cli.session import Action, Param, ModParam, ModNewParam, RmParam, Entity
from growbies.db.engine import get_db_engine
from growbies.db.models.session import Session, Sessions
from growbies.utils.report import decode_escapes

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[Session | Sessions]:
    engine = get_db_engine()

    session_name = cmd.kw.pop(commonParam.FUZZY_ID, None)
    action = cmd.kw.pop(Param.ACTION)

    if action in (Action.ACTIVATE, Action.DEACTIVATE):
        sess = engine.session.get(session_name)
        if action == Action.ACTIVATE:
            sess.active = True
        else:
            sess.active = False
        engine.session.upsert(sess)
    elif action in (Action.ADD, Action.RM):
        if action == Action.ADD:
            engine.session.add_entity(session_name, Entity.DEVICE, *cmd.kw.pop(Entity.DEVICE, ()))
            engine.session.add_entity(session_name, Entity.PROJECT, *cmd.kw.pop(Entity.PROJECT, ()))
            engine.session.add_entity(session_name, Entity.TAG, *cmd.kw.pop(Entity.TAG, ()))
            engine.session.add_entity(session_name, Entity.USER, *cmd.kw.pop(Entity.USER, ()))
        else:
            remove_self = cmd.kw.pop(RmParam.SELF, None)
            if remove_self:
                engine.session.remove(session_name)
            else:
                engine.session.remove_entity(session_name, Entity.DEVICE,
                                             *cmd.kw.pop(Entity.DEVICE, ()))
                engine.session.remove_entity(session_name, Entity.PROJECT,
                                             *cmd.kw.pop(Entity.PROJECT, ()))
                engine.session.remove_entity(session_name, Entity.TAG,
                                             *cmd.kw.pop(Entity.TAG, ()))
                engine.session.remove_entity(session_name, Entity.USER,
                                             *cmd.kw.pop(Entity.USER, ()))
    elif action in (Action.MOD, Action.NEW):
        if action == Action.NEW:
            sess = Session(name=session_name)
        else: # action == Action.MOD:
            sess = engine.session.get(session_name)

        new_name: Optional[str] = cmd.kw.pop(ModParam.NEW_NAME, None)
        description = cmd.kw.pop(ModNewParam.DESCRIPTION)
        meta = cmd.kw.pop(ModNewParam.META)
        notes = cmd.kw.pop(ModNewParam.NOTES)

        if new_name is not None:
            sess.name = new_name
        if description is not None:
            sess.description = decode_escapes(description)
        if meta is not None:
            sess.meta = meta
        if notes is not None:
            sess.notes = decode_escapes(notes)

        engine.session.upsert(sess)
        return None
    elif action == Action.LS:
        return engine.session.get(session_name)
    else:
        pr = cProfile.Profile()
        pr.enable()
        resp = engine.session.list()
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        logger.error("cProfile results:\n" + s.getvalue())
        return resp
    return None
