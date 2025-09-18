import ctypes

from . import nvm
from .common import BaseStructure
from growbies.utils.ctypes_utils import get_ctypes_2d_array, set_ctypes_2d_array
from growbies.utils.report import format_float_list, format_float_table

class Calibration(BaseStructure):
    COEFF_COUNT = 3
    MASS_SENSOR_COUNT = 5

    class Field(BaseStructure.Field):
        MASS_TEMP_COEFF = '_mass_temp_coeff'
        MASS_COEFF = '_mass_coeff'

    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * COEFF_COUNT
    _fields_ = [
        (Field.MASS_TEMP_COEFF, _row * MASS_SENSOR_COUNT),
        (Field.MASS_COEFF, ctypes.c_float * COEFF_COUNT),
    ]

    @property
    def mass_temp_coeff(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMP_COEFF)
        return get_ctypes_2d_array(ctypes_2d_array)

    @mass_temp_coeff.setter
    def mass_temp_coeff(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMP_COEFF)
        set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def mass_coeff(self) -> list[float]:
        return list(getattr(self, self.Field.MASS_COEFF))

    @mass_coeff.setter
    def mass_coeff(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.MASS_COEFF))):
            getattr(self, self.Field.MASS_COEFF)[idx] = values[idx]

    def __str__(self):
        coeff_columns = [f'Coeff {idx}' for idx in range(self.COEFF_COUNT)]
        sensor_coeff_columns = ['Sensor'] + coeff_columns

        str_list = [
            format_float_table('Mass/Temperature Correction',
                               sensor_coeff_columns,
                               self.mass_temp_coeff),
            format_float_list('Mass Calibration Coefficients', coeff_columns, self.mass_coeff),
        ]

        return '\n'.join(str_list)


class NvmCalibration(nvm.BaseNvm):
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Calibration)
    ]

