import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import PositionalParam
from growbies.cli.read import Param
from growbies.device.common.read import DataPoint
from growbies.device.cmd import ReadDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> DataPoint:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    raw = cmd.kw.pop(Param.RAW)
    times = cmd.kw.pop(Param.TIMES)

    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    return worker.cmd(ReadDeviceCmd(raw=raw, times=times))
