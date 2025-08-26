from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.service.cmd.structs import LoopbackServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import LoopbackDeviceCmd
from growbies.intf.resp import VoidDeviceResp
from growbies.worker.pool import get_pool


def loopback(cmd: LoopbackServiceCmd) -> ServiceCmdError | VoidDeviceResp:
    try:
        device_id = serials_to_device_ids(cmd.serial)[0]
    except ServiceCmdError as err:
        return err

    pool = get_pool()

    try:
        worker = pool.workers[device_id]
    except KeyError:
        return ServiceCmdError(f'Serial number "{cmd.serial}" is inactive.')


    return worker.cmd(LoopbackDeviceCmd())
