from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import internal_to_external_field, PositionalParam
from growbies.device.common import calibration as cal_mod
from growbies.device.cmd import GetCalibrationDeviceCmd, SetCalibrationDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    INIT = 'init'

def _init(worker):
    cmd = SetCalibrationDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[cal_mod.Calibration]:
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

    cal: cal_mod.Calibration = worker.cmd(GetCalibrationDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return cal.payload

    mass_temp_coeffs_list = cmd.kw.pop(
        internal_to_external_field(cal_mod.Calibration.Field.MASS_TEMP_COEFF), list())
    matrix = cal.payload.mass_temp_coeff
    for mass_temp_coeffs in mass_temp_coeffs_list:
        sensor = int(mass_temp_coeffs[0])
        coeffs = mass_temp_coeffs[1:]
        try:
            matrix[sensor] = coeffs
        except IndexError:
            raise ServiceCmdError(
                f'Index out of range for sensor {sensor} and coeff count {len(coeffs)}. '
                f'Matrix dimensions '
                f'[{cal_mod.Calibration.MASS_SENSOR_COUNT}]'
                f'[{cal_mod.Calibration.COEFF_COUNT}].')
    cal.payload.mass_temp_coeff = matrix

    mass_coeff_list = cmd.kw.pop(internal_to_external_field(cal_mod.Calibration.Field.MASS_COEFF),
                                 list())
    if mass_coeff_list:
        cal.payload.mass_coeff = mass_coeff_list

    cmd = SetCalibrationDeviceCmd(calibration=cal)

    _ = worker.cmd(cmd)
    return None
