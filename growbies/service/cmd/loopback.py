from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import PositionalParam
from growbies.device.cmd import LoopbackDeviceCmd
from growbies.device.resp import VoidDeviceResp
from growbies.worker.pool import get_pool

def execute(cmd: ServiceCmd) -> VoidDeviceResp:
    """
    raises:
        :class:`ServiceCmdError`
        :class:`DeviceError`
    """

    pool = get_pool()
    device = serials_to_devices(cmd.kw[PositionalParam.SERIAL])[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    return worker.cmd(LoopbackDeviceCmd())
