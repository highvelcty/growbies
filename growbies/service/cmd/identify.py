from growbies.service.cmd.structs import GetIdServiceCmd
from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import GetIdentifyDeviceCmd
from growbies.worker.pool import get_pool

def get(cmd: GetIdServiceCmd):
    try:
        device_id = serials_to_device_ids(cmd.serial)[0]
    except ServiceCmdError as err:
        return err

    pool = get_pool()

    try:
        worker = pool.workers[device_id]
    except KeyError:
        return ServiceCmdError(f'Serial number "{cmd.serial}" is inactive.')

    return worker.cmd(GetIdentifyDeviceCmd())
