from typing import Optional
import logging

from ..common import ServiceCmd
from growbies.cli.common import Param
from growbies.cli.thermal import ModParam
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

    activate = cmd.kw.pop(ModParam.ACTIVATE, None)
    mode = cmd.kw.pop(ModParam.MODE, None)
    duty_cycle = cmd.kw.pop(ModParam.DUTY_CYCLE, None)
    set_point = cmd.kw.pop(ModParam.SET_POINT, None)

    thermal_device_state: ThermalDeviceState = worker.cmd(GetThermalDeviceStateCmd())

    # if we need to write new state back to the device.
    if any(x is not None for x in (activate, mode, duty_cycle, set_point)):
        cmd = SetThermalDeviceStateCmd.from_buffer(thermal_device_state.control)
        if activate is not None:
            cmd.control.active = activate
        if mode is not None:
            cmd.control.mode = mode
        if duty_cycle is not None:
            cmd.control.duty_cycle = duty_cycle
        if set_point is not None:
            cmd.control.set_point = set_point

        logger.error(f'emey:\n{cmd}')
        worker.cmd(cmd)

        return None
    else:
        return thermal_device_state
