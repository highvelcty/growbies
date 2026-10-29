import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.cli.common import Param as CommonParam
from growbies.cli.read import Param
from growbies.db.engine import get_db_engine
from growbies.protocol.common.read import DataPoint
from growbies.protocol.cmd import ReadDeviceCmd
from growbies.service.cmd.ls import get_device_monitor_singleton
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> DataPoint:
    engine = get_db_engine()
    pool = get_pool()
    device = get_device_monitor_singleton().devices.get(cmd.kw.pop(CommonParam.FUZZY_ID))

    ref_mass = cmd.kw.pop(Param.REF_MASS, None)
    reset = cmd.kw.pop(Param.RESET, False)
    sensor_ref_mass = cmd.kw.pop(Param.SENSOR_REF_MASS, None)
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    return worker.cmd(ReadDeviceCmd(ref_mass, sensor_ref_mass, reset))
