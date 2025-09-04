import logging

from growbies.service.cli import serials_to_devices
from growbies.service.cmd.structs import IdServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.intf.common import TIdentify
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def get_or_set(cmd: IdServiceCmd) -> TIdentify:
    pool = get_pool()

    device = serials_to_devices(cmd.serial)[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    identify: TIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.device_cmd_kw.values()):
        return identify

    for key, val in cmd.device_cmd_kw.items():
        if getattr(identify, key) is None:
            raise ServiceCmdError(f'Identify version {identify.hdr.version} does not support the '
                                  f'"{key}" field.')
        if val is not None:
            setattr(identify, key, val)

    cmd = SetIdentifyDeviceCmd(payload=identify)

    _ = worker.cmd(cmd)

    return worker.cmd(GetIdentifyDeviceCmd())
