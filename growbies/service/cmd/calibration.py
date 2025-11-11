from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from ..utils import serials_to_devices
from growbies.cli.common import internal_to_external_field, PositionalParam
from growbies.device.common import calibration as cal_mod
from growbies.device.cmd import (GetCalibrationDeviceCmd, SetCalibrationDeviceCmd,
                                 SetCalibrationDeviceCmd2)
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    INIT = 'init'

def _init(worker):
    cmd = SetCalibrationDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[cal_mod.Calibration | cal_mod.Calibration2]:
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

    nvm_cal: cal_mod.Calibration | cal_mod.Calibration2 = worker.cmd(GetCalibrationDeviceCmd())
    version = nvm_cal.hdr.version
    cal = nvm_cal.payload


    if all(value is None for value in cmd.kw.values()):
        return cal

    _exc_coeff_out_of_range = ServiceCmdError(f'Coefficient count out of range. Max is '
                                              f'{cal.get_max_coeff_count()} ')

    mass_temp_coeffs_list = cmd.kw.pop(
        internal_to_external_field(cal_mod.Calibration.Field.MASS_TEMP_COEFF), list())
    matrix = cal.mass_temp_coeff
    for mass_temp_coeffs in mass_temp_coeffs_list:
        sensor = int(mass_temp_coeffs[0])
        coeffs = mass_temp_coeffs[1:]
        try:
            matrix[sensor] = coeffs
        except IndexError:
            raise ServiceCmdError(f'Sensor index out of range. '
                                  f'Max is {cal.get_max_sensor_count()}')
    try:
        cal.mass_temp_coeff = matrix
    except IndexError:
        raise _exc_coeff_out_of_range

    mass_coeff_list = cmd.kw.pop(internal_to_external_field(cal_mod.Calibration.Field.MASS_COEFF),
                                 list())
    if mass_coeff_list:
        try:
            cal.mass_coeff = mass_coeff_list
        except IndexError:
            raise _exc_coeff_out_of_range

    if version == 1:
        cmd = SetCalibrationDeviceCmd(calibration=nvm_cal)
    else:
        cmd = SetCalibrationDeviceCmd2(calibration=nvm_cal)

    _ = worker.cmd(cmd)
    return None
