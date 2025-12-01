from typing import Optional
import logging

from . import ls
from ..common import ServiceCmd
from growbies.cli.device import Action, Param, ModParam, ReadParam
from growbies.db.engine import get_db_engine
from growbies.db.models.device import Device, Devices
from growbies.worker.pool import get_pool


logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[Device | Devices]:
    engine = get_db_engine()

    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    action = cmd.kw.pop(Param.ACTION)

    if action in (Action.ACTIVATE, Action.DEACTIVATE):
        dev = engine.device.get(fuzzy_id)
        worker_pool = get_pool()
        if action == Action.ACTIVATE:
            engine.device.set_active(dev.id)
            worker_pool.connect(dev.id)
        else:
            engine.device.clear_active(dev.id)
            worker_pool.disconnect(dev.id)
            worker_pool.join_all(dev.id)
    elif action in (None, Action.LS):
        if fuzzy_id:
            return engine.device.get(fuzzy_id)
        else:
            return ls.execute()
    elif action == Action.MOD:
        new_name = cmd.kw.pop(ModParam.NAME)
        dev = engine.device.get(fuzzy_id)
        dev.name = new_name
        engine.device.upsert(dev)
    return None
