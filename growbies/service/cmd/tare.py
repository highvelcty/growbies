from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import PositionalParam
from growbies.cli.tare import Param
from growbies.device.common import tare as tare_mod
from growbies.device.cmd import GetTareDeviceCmd, SetTareDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def _init(worker):
    cmd = SetTareDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[tare_mod.Tare]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    index = cmd.kw.pop(Param.INDEX)
    value = cmd.kw.pop(Param.VALUE)
    if (index is None and value is not None) or (index is not None and value is None):
        raise ServiceCmdError(f'Tare index and value must be provided together.')

    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    tare: tare_mod.NvmTare = worker.cmd(GetTareDeviceCmd())

    if index is None:
        return tare.payload

    existing = tare.payload.values
    try:
        existing[index] = value
    except IndexError:
        raise ServiceCmdError(
            f'Index out of range, length of tare array is {tare_mod.Tare.TARE_COUNT}.')

    tare.payload.values = existing

    cmd = SetTareDeviceCmd(tare=tare)

    _ = worker.cmd(cmd)
    return None
