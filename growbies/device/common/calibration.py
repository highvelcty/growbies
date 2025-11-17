import ctypes
import logging

from . import nvm
from .common import BaseStructure, BaseUnion
from growbies.utils.ctypes_utils import get_ctypes_2d_array, set_ctypes_2d_array
from growbies.utils.report import format_float_list, format_float_table

logger = logging.getLogger(__name__)

class CalibrationHdr(BaseStructure):
    MAX_MASS_SENSOR_COUNT = 5
    MAX_COEFFS_COUNT = 6
    REF_TEMPERATURE = 25.0

    class Field(BaseStructure.Field):
        MASS_SENSOR_COUNT = '_mass_sensor_count'
        COEFF_COUNT = '_coeff_count'
        REF_TEMPERATURE = '_ref_temperature'
        RESERVED = '_reserved'

    _fields_ = [
        (Field.MASS_SENSOR_COUNT, ctypes.c_uint8),
        (Field.COEFF_COUNT, ctypes.c_uint8),
        (Field.REF_TEMPERATURE, ctypes.c_float),
        (Field.RESERVED, ctypes.c_uint16)
    ]


    def __init__(self):
        super().__init__()
        self.mass_sensor_count = self.MAX_MASS_SENSOR_COUNT
        self.coeff_count = self.MAX_COEFFS_COUNT
        self.ref_temperature = self.REF_TEMPERATURE  # or some default

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

    @property
    def ref_temperature(self) -> float:
        return getattr(self, self.Field.REF_TEMPERATURE)

    @ref_temperature.setter
    def ref_temperature(self, value: float):
        setattr(self, self.Field.REF_TEMPERATURE, value)

    @property
    def reserved(self):
        return getattr(self, self.Field.RESERVED)

    @reserved.setter
    def reserved(self, value: int):
        setattr(self, self.Field.RESERVED, value)

class Coeffs(BaseStructure):
    class Field(BaseStructure.Field):
        MASS_OFFSET = '_mass_offset'
        MASS_SLOPE = '_mass_slope'
        TEMPERATURE_SLOPE = '_temperature_slope'
        MASS_CROSS_TEMPERATURE = '_mass_cross_temperature'
        QUADRATIC_TEMPERATURE = '_quadratic_temperature'
        QUADRATIC_MASS = '_quadratic_mass'

    _fields_ = [
        (Field.MASS_OFFSET, ctypes.c_float),
        (Field.MASS_SLOPE, ctypes.c_float),
        (Field.TEMPERATURE_SLOPE, ctypes.c_float),
        (Field.MASS_CROSS_TEMPERATURE, ctypes.c_float),
        (Field.QUADRATIC_TEMPERATURE, ctypes.c_float),
        (Field.QUADRATIC_MASS, ctypes.c_float)
    ]

    @property
    def mass_offset(self) -> float:
        return getattr(self, self.Field.MASS_OFFSET)

    @mass_offset.setter
    def mass_offset(self, value: float):
        setattr(self, self.Field.MASS_OFFSET, value)

    @property
    def mass_slope(self) -> float:
        return getattr(self, self.Field.MASS_SLOPE)

    @mass_slope.setter
    def mass_slope(self, value: float):
        setattr(self, self.Field.MASS_SLOPE, value)

    @property
    def temperature_slope(self) -> float:
        return getattr(self, self.Field.TEMPERATURE_SLOPE)

    @temperature_slope.setter
    def temperature_slope(self, value: float):
        setattr(self, self.Field.TEMPERATURE_SLOPE, value)

    @property
    def mass_cross_temperature(self) -> float:
        return getattr(self, self.Field.MASS_CROSS_TEMPERATURE)

    @mass_cross_temperature.setter
    def mass_cross_temperature(self, value: float):
        setattr(self, self.Field.MASS_CROSS_TEMPERATURE, value)

    @property
    def quadratic_temperature(self) -> float:
        return getattr(self, self.Field.QUADRATIC_TEMPERATURE)

    @quadratic_temperature.setter
    def quadratic_temperature(self, value: float):
        setattr(self, self.Field.QUADRATIC_TEMPERATURE, value)

    @property
    def quadratic_mass(self) -> float:
        return getattr(self, self.Field.QUADRATIC_MASS)

    @quadratic_mass.setter
    def quadratic_mass(self, value: float):
        setattr(self, self.Field.QUADRATIC_MASS, value)

class SensorCalibration(BaseUnion):
    class Field(BaseUnion.Field):
        COEFFS = '_coeffs'
        RAW = '_raw'

    _fields_ = [
        (Field.COEFFS, Coeffs),
        (Field.RAW, ctypes.c_float * CalibrationHdr.MAX_COEFFS_COUNT)
    ]

    @property
    def coeffs(self) -> Coeffs:
        return getattr(self, self.Field.COEFFS)

    @coeffs.setter
    def coeffs(self, value: Coeffs):
        setattr(self, self.Field.COEFFS, value)

    @property
    def raw(self) -> ctypes.Array[float]:
        return getattr(self, self.Field.RAW)

class Calibration(BaseStructure):

    class Field(BaseStructure.Field):
        HDR = '_hdr'
        SENSOR = '_sensor'

    _fields_ = [
        (Field.HDR, CalibrationHdr),
        (Field.SENSOR, SensorCalibration * CalibrationHdr.MAX_MASS_SENSOR_COUNT)
    ]

    def __init__(self):
        super().__init__()
        setattr(self, self.Field.HDR, CalibrationHdr())

    @property
    def hdr(self) -> CalibrationHdr:
        return getattr(self, self.Field.HDR)

    @property
    def sensor(self) -> SensorCalibration:
        return getattr(self, self.Field.SENSOR)

    def __str__(self):
        max_cols = ['Sensor', 'M Off', 'M Slope', 'T Slope', 'M x T', 'T^2', 'M^2']

        cols = max_cols[:1 + self.hdr.coeff_count]
        datas = []
        for sensor_idx in range(self.hdr.mass_sensor_count):
            # Include only the first coeff_count coefficients
            row = [sensor_idx] + self.sensor[sensor_idx].raw[:self.hdr.coeff_count]
            datas.append(row)

        # Use PrettyTable formatter
        table_str = format_float_list('Mass Calibration Coefficients', cols, datas)
        return table_str

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
