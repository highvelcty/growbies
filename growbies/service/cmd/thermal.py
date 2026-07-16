from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError, ServiceOp
from growbies.cli.common import Param
from growbies.cli.thermal import Action, ModParam
from growbies.db.engine import get_db_engine
from growbies.protocol.cmd import GetThermalCfgCmd, SetThermalCfgCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    engine = get_db_engine()
    pool = get_pool()
    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    device = engine.device.get(fuzzy_id)

    action = cmd.kw.pop(Param.ACTION, None)
    activate = cmd.kw.pop(ModParam.ACTIVATE, None)
    set_point = cmd.kw.pop(ModParam.SET_POINT, False)

    worker = pool.get_if_active_only(device.id)

    if action == Action.CFG:
        if activate or set_point:
            cmd = SetThermalCfgCmd()
            cmd.action = activate
            cmd.set_point = set_point
        else:
            cmd = GetThermalCfgCmd()
    else:
        raise ServiceCmdError(f'Invalid {ServiceOp.THERMAL} sub-cmd "{action}".')


    return worker.cmd(cmd)