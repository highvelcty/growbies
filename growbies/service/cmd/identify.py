from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import PositionalParam
from growbies.cli.identify import Param
from growbies.device.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.device.common import identify as id_mod
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def _init(worker):
    cmd = SetIdentifyDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[id_mod.Identify1]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    ident: id_mod.NvmIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return ident.payload

    for key, val in cmd.kw.items():
        if getattr(ident.payload, key, None) is None:
            raise ServiceCmdError(f'Identify version {ident.VERSION} does not support the '
                                  f'"{key}" field.')
        if val is not None:
            setattr(ident.payload, key, val)

    cmd = SetIdentifyDeviceCmd()
    cmd.identify = ident
    _ = worker.cmd(cmd)
    return None
