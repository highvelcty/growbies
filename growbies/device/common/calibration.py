import ctypes
import logging

from . import nvm
from .common import BaseStructure
from growbies.utils.ctypes_utils import get_ctypes_2d_array, set_ctypes_2d_array
from growbies.utils.report import format_float_list, format_float_table

logger = logging.getLogger(__name__)

class CalibrationHdr(BaseStructure):
    class Field(BaseStructure.Field):
        MASS_SENSOR_COUNT = '_mass_sensor_count'
        COEFF_COUNT = '_coeff_count'
        RESERVED = '_reserved'

    _fields_ = [
        (Field.MASS_SENSOR_COUNT, ctypes.c_uint8),
        (Field.COEFF_COUNT, ctypes.c_uint8),
        (Field.RESERVED, ctypes.c_uint16)
    ]

    @property
    def mass_sensor_count(self) -> int:
        return getattr(self, self.Field.MASS_SENSOR_COUNT)

    @mass_sensor_count.setter
    def mass_sensor_count(self, value: int):
        setattr(self, self.Field.MASS_SENSOR_COUNT, value)

    @property
    def coeff_count(self) -> int:
        return getattr(self, self.Field.COEFF_COUNT)

    @coeff_count.setter
    def coeff_count(self, value: int):
        setattr(self, self.Field.COEFF_COUNT, value)


class CalibrationBase(BaseStructure):
    _MAX_COEFF_COUNT = 1
    _MASS_SENSOR_COUNT = 1

    class Field(BaseStructure.Field):
        MASS_TEMP_COEFF = '_mass_temp_coeff'
        MASS_COEFF = '_mass_coeff'

    @classmethod
    def get_max_coeff_count(cls) -> int:
        return cls._MAX_COEFF_COUNT

    @classmethod
    def get_max_sensor_count(cls) -> int:
        return cls._MASS_SENSOR_COUNT

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
        for idx, value in enumerate(values):
            getattr(self, self.Field.MASS_COEFF)[idx] = value

class Calibration(CalibrationBase):
    _MAX_COEFF_COUNT = 3
    _MASS_SENSOR_COUNT = 5

    class Field(BaseStructure.Field):
        MASS_TEMP_COEFF = '_mass_temp_coeff'
        MASS_COEFF = '_mass_coeff'

    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * _MAX_COEFF_COUNT
    _fields_ = [
        (Field.MASS_TEMP_COEFF, _row * _MASS_SENSOR_COUNT),
        (Field.MASS_COEFF, ctypes.c_float * _MAX_COEFF_COUNT),
    ]

    def __str__(self):
        coeff_columns = [f'Coeff {idx}' for idx in range(self.MAX_COEFF_COUNT)]
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

    @property
    def payload(self) -> Calibration:
        return super().payload

    @payload.setter
    def payload(self, value: Calibration):
        super().payload = value

class Calibration2(CalibrationBase):
    _MAX_COEFF_COUNT = 4
    _MAX_SENSOR_COUNT = 5

    class Field(BaseStructure.Field):
        HDR = '_hdr'
        MASS_TEMP_COEFF = '_mass_temp_coeff'
        MASS_COEFF = '_mass_coeff'

    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * _MAX_COEFF_COUNT
    _fields_ = [
        (Field.HDR, CalibrationHdr),
        (Field.MASS_TEMP_COEFF, _row * _MAX_SENSOR_COUNT),
        (Field.MASS_COEFF, ctypes.c_float * _MAX_COEFF_COUNT),
    ]

    @property
    def hdr(self) -> CalibrationHdr:
        return getattr(self, self.Field.HDR)

    def __str__(self):
        coeff_count = self.hdr.coeff_count
        sensor_count = self.hdr.mass_sensor_count

        coeff_columns = [f'Coeff {idx}' for idx in range(coeff_count)]
        sensor_coeff_columns = ['Sensor'] + coeff_columns

        mass_temp = [list(self.mass_temp_coeff[i][:coeff_count]) for i in range(sensor_count)]
        mass_coeffs = self.mass_coeff[:coeff_count]

        str_list = [
            format_float_table('Mass/Temperature Correction',
                               sensor_coeff_columns,
                               mass_temp),
            format_float_list('Mass Calibration Coefficients', coeff_columns, mass_coeffs),
        ]

        return '\n'.join(str_list)


class NvmCalibration2(nvm.BaseNvm):
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Calibration2)
    ]

    @property
    def payload(self) -> Calibration2:
        return super().payload

    @payload.setter
    def payload(self, value: Calibration2):
        super().payload = value