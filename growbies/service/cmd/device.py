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

    action = cmd.kw.pop(Param.ACTION)

    if action in (Action.ACTIVATE, Action.DEACTIVATE):
        dev = ls.get_device_monitor_singleton().devices.get(cmd.kw.pop(Param.FUZZY_ID))
        if action == Action.ACTIVATE:
            engine.device.set_active(dev.id)
        else:
            engine.device.clear_active(dev.id)
        callback()
    elif action in (None, Action.LS):
        fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
        if fuzzy_id is not None:
            return ls.get_device_monitor_singleton().devices.get(fuzzy_id)
        else:
            return ls.get_device_monitor_singleton().rescan()
    elif action == Action.MOD:
        new_name = cmd.kw.pop(ModParam.NAME)
        dev = ls.get_device_monitor_singleton().devices.get(cmd.kw.pop(Param.FUZZY_ID))
        dev.name = new_name
        engine.device.upsert(dev)
    return None
