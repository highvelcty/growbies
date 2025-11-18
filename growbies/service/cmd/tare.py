from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import PositionalParam
from growbies.cli.tare import Param
from growbies.db.engine import get_db_engine
from growbies.device.common import tare as tare_mod
from growbies.device.cmd import GetTareDeviceCmd, SetTareDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def _init(worker):
    cmd = SetTareDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[tare_mod.Tares]:
    engine = get_db_engine()
    pool = get_pool()

    fuzzy_id = cmd.kw.pop(PositionalParam.FUZZY_ID, None)
    init = cmd.kw.pop(Param.INIT)
    slot = cmd.kw.pop(Param.SLOT)
    value = cmd.kw.pop(Param.VALUE)
    display_units = cmd.kw.pop(Param.DISPLAY_UNITS)

    device = engine.device.get(fuzzy_id)
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Device "{device.name}" is inactive.')

    if init:
        _init(worker)
        return None

    tare: tare_mod.NvmTare = worker.cmd(GetTareDeviceCmd())

    if slot is None:
        return tare.payload

    if (value is not None or display_units is not None) and slot is None:
        raise ServiceCmdError('Slot must be provided to set attributes.')

    if slot >= len(tare.payload.tares) or slot < 0:
        raise ServiceCmdError(f'Slot index must be within range '
                              f'[0, {len(tare.payload.tares) - 1}].')
    if value is not None:
        tare.payload.tares[slot].value = value
    if display_units is not None:
        tare.payload.tares[slot].display_units = display_units

    cmd = SetTareDeviceCmd(tare=tare)

    _ = worker.cmd(cmd)
    return None
