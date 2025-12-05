from typing import Optional
import logging

from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.device.common import calibration as cal_mod
from growbies.device.cmd import GetCalibrationDeviceCmd, SetCalibrationDeviceCmd
from growbies.service.common import ServiceCmd, ServiceCmdError
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    INIT = 'init'

def _init(worker):
    cmd = SetCalibrationDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[cal_mod.Calibration]:
    engine = get_db_engine()
    pool = get_pool()
    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID, None)
    device = engine.device.get(fuzzy_id)

    init = cmd.kw.pop(Param.INIT)
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    nvm_cal: cal_mod.NvmCalibration = worker.cmd(GetCalibrationDeviceCmd())
    cal: cal_mod.Calibration = nvm_cal.payload


    if all(value is None for value in cmd.kw.values()):
        return cal

    coeff_sets = cmd.kw.pop(cal_mod.SensorCalibration.Field.COEFFS.public_name, list())
    for coeff_set in coeff_sets:
        sensor = int(coeff_set[0])
        coeffs = coeff_set[1:]

        max_sensor_idx = cal.hdr.mass_sensor_count - 1
        max_coeffs_count = cal.hdr.coeff_count
        if sensor > max_sensor_idx:
            raise ServiceCmdError(f'Sensor index out of range. Max is {max_sensor_idx}')
        if len(coeffs) > max_coeffs_count:
            raise ServiceCmdError(f'Coefficient list length of {len(coeffs)} exceeds maximum '
                                  f'length of {max_coeffs_count}')

        for idx, coeff in enumerate(coeffs):
            cal.sensor[sensor].raw[idx] = coeff

    cmd = SetCalibrationDeviceCmd(calibration=nvm_cal)

    _ = worker.cmd(cmd)
    return None
