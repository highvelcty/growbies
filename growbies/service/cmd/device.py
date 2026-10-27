from typing import Callable, Optional
import logging

from . import ls
from ..common import ServiceCmd
from growbies.cli.device import Action, Param, ModParam
from growbies.db.engine import get_db_engine
from growbies.db.models.device import Device, Devices

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd, callback: Callable) -> Optional[Device | Devices]:
    engine = get_db_engine()

    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    action = cmd.kw.pop(Param.ACTION)

    if action in (Action.ACTIVATE, Action.DEACTIVATE):
        dev = engine.device.get(fuzzy_id)
        if action == Action.ACTIVATE:
            engine.device.set_active(dev.id)
        else:
            engine.device.clear_active(dev.id)
        callback()
    elif action in (None, Action.LS):
        if fuzzy_id:
            return engine.device.get(fuzzy_id)
        else:
            return ls.get_device_monitor_singleton().rescan()
    elif action == Action.MOD:
        new_name = cmd.kw.pop(ModParam.NAME)
        dev = engine.device.get(fuzzy_id)
        dev.name = new_name
        engine.device.upsert(dev)
    return None
