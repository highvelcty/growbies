from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError, ServiceOp
from growbies.cli.common import Param
from growbies.cli.thermal import Action, ModParam
from growbies.db.engine import get_db_engine
from growbies.protocol.cmd import GetThermalDeviceStateCmd, SetThermalDeviceStateCmd
from growbies.protocol.common.thermal import ThermalDeviceState
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[ThermalDeviceState]:
    engine = get_db_engine()
    pool = get_pool()
    fuzzy_id = cmd.kw.pop(Param.FUZZY_ID, None)
    device = engine.device.get(fuzzy_id)
    worker = pool.get_if_active_only(device.id)

    action = cmd.kw.pop(Param.ACTION, None)
    if action == Action.STATE:
        activate = cmd.kw.pop(ModParam.ACTIVATE, None)
        mode = cmd.kw.pop(ModParam.MODE, None)
        duty_cycle = cmd.kw.pop(ModParam.DUTY_CYCLE, None)
        set_point = cmd.kw.pop(ModParam.SET_POINT, None)

        thermal_device_state: ThermalDeviceState = worker.cmd(GetThermalDeviceStateCmd())

        # if we need to write new state back to the device.
        if any(x is not None for x in (activate, mode, duty_cycle, set_point)):
            cmd = SetThermalDeviceStateCmd.from_buffer(thermal_device_state)
            cmd.state.active = activate
            cmd.state.mode = mode
            cmd.state.duty_cycle = duty_cycle
            cmd.state.set_point = set_point
            worker.cmd(cmd)

            return None
        else:
            return thermal_device_state
    else:
        raise ServiceCmdError(f'Invalid {ServiceOp.THERMAL} sub-cmd "{action}".')
