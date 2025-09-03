from growbies.service.cmd.structs import GetIdServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.intf.cmd import GetIdentifyDeviceCmd
from growbies.intf.common import TIdentify
from growbies.worker.pool import get_pool

def get(cmd: GetIdServiceCmd) -> TIdentify:
    """
    raises:
        :class:`ServiceCmdError`
        :class:`DeviceError`
    """
    pool = get_pool()
    try:
        worker = pool.workers[serials_to_device_ids(cmd.serial)[0]]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{cmd.serial}" is inactive.')
    return worker.cmd(GetIdentifyDeviceCmd())
