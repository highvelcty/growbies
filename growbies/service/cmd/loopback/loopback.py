from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.service.cmd.structs import LoopbackServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import LoopbackDeviceCmd
from growbies.intf.resp import VoidDeviceResp
from growbies.worker.pool import get_pool


def loopback(cmd: LoopbackServiceCmd) -> VoidDeviceResp:
    """
    raises:
        :class:`ServiceCmdError`
        :class:`DeviceError`
    """

    pool = get_pool()
    device_id = serials_to_device_ids(cmd.serial)[0]

    try:
        worker = pool.workers[device_id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{cmd.serial}" is inactive.')

    return worker.cmd(LoopbackDeviceCmd())
