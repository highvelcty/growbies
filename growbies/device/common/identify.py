from ctypes import sizeof
from datetime import datetime
from enum import IntEnum, StrEnum
from typing import NewType
import ctypes

from packaging.version import InvalidVersion, Version

from . import nvm
from .common import BaseStructure, MassUnitsType
from growbies.utils import timestamp
from growbies.utils.ctypes_utils import cstring_to_str
from growbies.utils.types import Serial_t, ModelNumber_t


class BatteryType(IntEnum):
    GENERIC = 0

class DisplayType(IntEnum):
    GENERIC = 0

class LedType(IntEnum):
    GENERIC = 0

class FrameType(IntEnum):
    GENERIC = 0

class FootType(IntEnum):
    GENERIC = 0

class MassSensorType(IntEnum):
    GENERIC = 0

class PcbaType(IntEnum):
    ARDUINO = 0
    ESP32C3 = 1

class TemperatureSensorType(IntEnum):
    GENERIC = 0

class TemperatureUnitsType(IntEnum):
    FAHRENHEIT = 0
    CELSIUS = 1

class WirelessType(IntEnum):
    NONE = 0
    BLE = 1

class IdentifyVersion(IntEnum):
    ZERO = 0
    ONE = 1

class IdentifyHeader(BaseStructure): pass

class Identify(BaseStructure):
    class Field(BaseStructure.Field):
        FIRMWARE_VERSION = '_firmware_version'
        SERIAL_NUMBER = '_serial_number'
        MODEL_NUMBER = '_model_number'
        MANUFACTURE_DATE = '_manufacture_date'
        MASS_SENSOR_COUNT = '_mass_sensor_count'
        MASS_SENSOR_TYPE = '_mass_sensor_type'
        TEMPERATURE_SENSOR_COUNT = '_temperature_sensor_count'
        TEMPERATURE_SENSOR_TYPE = '_temperature_sensor_type'
        PCBA = '_pcba'
        WIRELESS = '_wireless'
        BATTERY = '_battery'
        DISPLAY = '_display'
        LED = '_led'
        FRAME = '_frame'
        FOOT = '_foot'
        FLIP = '_flip'
        MASS_UNITS = '_mass_units'
        TEMPERATURE_UNITS = '_temperature_units'
        CONTRAST = '_contrast'
        TELEMETRY_INTERVAL = '_telemetry_interval'
        SLEEP_TIMEOUT = '_sleep_timeout'
        AUTO_WAKE_INTERVAL = '_auto_wake_interval'

    _fields_ = [
        (Field.FIRMWARE_VERSION, ctypes.c_char * 32),
    ]

    @property
    def firmware_version(self) -> Version | str:
        val = cstring_to_str(getattr(self, self.Field.FIRMWARE_VERSION))
        try:
            return Version(val)
        except InvalidVersion:
            return val

    @property
    def serial_number(self) -> Serial_t:
        return cstring_to_str(getattr(self, self.Field.SERIAL_NUMBER))

    @serial_number.setter
    def serial_number(self, value: Serial_t):
        setattr(self, self.Field.SERIAL_NUMBER, value.encode())

    @property
    def model_number(self) -> ModelNumber_t:
        return cstring_to_str(getattr(self, self.Field.MODEL_NUMBER))

    @model_number.setter
    def model_number(self, value: ModelNumber_t):
        setattr(self, self.Field.MODEL_NUMBER, value.encode())

    @property
    def manufacture_date(self) -> datetime:
        return timestamp.get_utc_dt(getattr(self, self.Field.MANUFACTURE_DATE))

    @manufacture_date.setter
    def manufacture_date(self, value: datetime):
        setattr(self, self.Field.MANUFACTURE_DATE, timestamp.get_unix_time(value))

    @property
    def mass_sensor_count(self) -> int:
        return getattr(self, self.Field.MASS_SENSOR_COUNT)

    @mass_sensor_count.setter
    def mass_sensor_count(self, value: int):
        setattr(self, self.Field.MASS_SENSOR_COUNT, value)

    @property
    def mass_sensor_type(self) -> MassSensorType | int:
        val = getattr(self, self.Field.MASS_SENSOR_TYPE)
        try:
            return MassSensorType(val)
        except ValueError:
            return val

    @mass_sensor_type.setter
    def mass_sensor_type(self, value: MassSensorType):
        setattr(self, self.Field.MASS_SENSOR_TYPE, value)

    @property
    def temperature_sensor_count(self) -> int:
        return getattr(self, self.Field.TEMPERATURE_SENSOR_COUNT)

    @temperature_sensor_count.setter
    def temperature_sensor_count(self, value: int):
        setattr(self, self.Field.TEMPERATURE_SENSOR_COUNT, value)

    @property
    def temperature_sensor_type(self) -> TemperatureSensorType:
        val = getattr(self, self.Field.TEMPERATURE_SENSOR_TYPE)
        try:
            return TemperatureSensorType(val)
        except ValueError:
            return val

    @temperature_sensor_type.setter
    def temperature_sensor_type(self, value: TemperatureSensorType):
        setattr(self, self.Field.TEMPERATURE_SENSOR_TYPE, value)

    @property
    def pcba(self) -> PcbaType:
        val = getattr(self, self.Field.PCBA)
        try:
            return PcbaType(val)
        except ValueError:
            return val

    @pcba.setter
    def pcba(self, value: PcbaType):
        setattr(self, self.Field.PCBA, PcbaType(value))

    @property
    def wireless(self) -> WirelessType:
        val = getattr(self, self.Field.WIRELESS)
        try:
            return WirelessType(val)
        except ValueError:
            return val

    @wireless.setter
    def wireless(self, value: WirelessType):
        setattr(self, self.Field.WIRELESS, value)

    @property
    def battery(self) -> BatteryType:
        val = getattr(self, self.Field.BATTERY)
        try:
            return BatteryType(val)
        except ValueError:
            return val

    @battery.setter
    def battery(self, value: BatteryType):
        setattr(self, self.Field.BATTERY, value)

    @property
    def display(self) -> DisplayType:
        val = getattr(self, self.Field.DISPLAY)
        try:
            return DisplayType(val)
        except ValueError:
            return val

    @display.setter
    def display(self, value: DisplayType):
        setattr(self, self.Field.DISPLAY, value)

    @property
    def led(self) -> LedType:
        val = getattr(self, self.Field.LED)
        try:
            return LedType(val)
        except ValueError:
            return val

    @led.setter
    def led(self, value: LedType):
        setattr(self, self.Field.LED, value)

    @property
    def frame(self) -> FrameType:
        val = getattr(self, self.Field.FRAME)
        try:
            return FrameType(val)
        except ValueError:
            return val

    @frame.setter
    def frame(self, value: FrameType):
        setattr(self, self.Field.FRAME, value)

    @property
    def foot(self) -> FootType:
        val = getattr(self, self.Field.FOOT)
        try:
            return FootType(val)
        except ValueError:
            return val

    @foot.setter
    def foot(self, value: FootType):
        setattr(self, self.Field.FOOT, value)

    @property
    def flip(self) -> bool:
        return getattr(self, self.Field.FLIP)

    @flip.setter
    def flip(self, value: bool):
        setattr(self, self.Field.FLIP, value)

    @property
    def mass_units(self) -> MassUnitsType:
        val = getattr(self, self.Field.MASS_UNITS)
        try:
            return MassUnitsType(val)
        except ValueError:
            return val

    @mass_units.setter
    def mass_units(self, value: MassUnitsType):
        setattr(self, self.Field.MASS_UNITS, value)

    @property
    def temperature_units(self) -> TemperatureUnitsType:
        val = getattr(self, self.Field.TEMPERATURE_UNITS)
        try:
            return TemperatureUnitsType(val)
        except ValueError:
            return val

    @temperature_units.setter
    def temperature_units(self, value: TemperatureUnitsType):
        setattr(self, self.Field.TEMPERATURE_UNITS, value)

    @property
    def contrast(self) -> int:
        return getattr(self, self.Field.CONTRAST)

    @contrast.setter
    def contrast(self, value: int):
        setattr(self, self.Field.CONTRAST, value)

    @property
    def telemetry_interval(self) -> float:
        return getattr(self, self.Field.TELEMETRY_INTERVAL)

    @telemetry_interval.setter
    def telemetry_interval(self, value: float):
        setattr(self, self.Field.TELEMETRY_INTERVAL, value)

    @property
    def sleep_timeout(self) -> float:
        return getattr(self, self.Field.SLEEP_TIMEOUT)

    @sleep_timeout.setter
    def sleep_timeout(self, value: float):
        setattr(self, self.Field.SLEEP_TIMEOUT, value)

    @property
    def auto_wake_interval(self) -> float:
        return getattr(self, self.Field.AUTO_WAKE_INTERVAL)

    @auto_wake_interval.setter
    def auto_wake_interval(self, value: float):
        setattr(self, self.Field.AUTO_WAKE_INTERVAL, value)

class Identify1(Identify):
    _fields_ = [
        (Identify.Field.SERIAL_NUMBER, ctypes.c_char * 32),
        (Identify.Field.MODEL_NUMBER, ctypes.c_char * 32),
        (Identify.Field.MANUFACTURE_DATE, ctypes.c_float),
        (Identify.Field.MASS_SENSOR_TYPE, ctypes.c_uint8),
        (Identify.Field.MASS_SENSOR_COUNT, ctypes.c_uint8),
        (Identify.Field.TEMPERATURE_SENSOR_TYPE, ctypes.c_uint8),
        (Identify.Field.TEMPERATURE_SENSOR_COUNT, ctypes.c_uint8),
        (Identify.Field.PCBA, ctypes.c_uint8),
        (Identify.Field.WIRELESS, ctypes.c_uint8),
        (Identify.Field.BATTERY, ctypes.c_uint8),
        (Identify.Field.DISPLAY, ctypes.c_uint8),
        (Identify.Field.LED, ctypes.c_uint8),
        (Identify.Field.FRAME, ctypes.c_uint8),
        (Identify.Field.FOOT, ctypes.c_uint8),
        (Identify.Field.FLIP, ctypes.c_bool),
    ]

class Identify2(Identify1):
    _fields_ = [
        (Identify.Field.MASS_UNITS, ctypes.c_uint8),
        (Identify.Field.TEMPERATURE_UNITS, ctypes.c_uint8),
    ]

class Identify3(Identify2):
    _fields_ = [
        (Identify.Field.CONTRAST, ctypes.c_uint8)
    ]

class Identify4(Identify3):
    # No change on gateway side
    pass

class Identify5(Identify4):
    _fields_ = [
        (Identify.Field.TELEMETRY_INTERVAL, ctypes.c_float)
    ]

class Identify6(Identify5):
    _fields_ = [
        (Identify.Field.SLEEP_TIMEOUT, ctypes.c_float)
    ]

class Identify7(Identify6):
    _fields_ = [
        (Identify.Field.AUTO_WAKE_INTERVAL, ctypes.c_float)
    ]

class BaseNvmIdentify(nvm.BaseNvm):
    @property
    def payload(self) -> Identify1:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify1):
        super().payload = value

TNvmIdentify = NewType('TNvmIdentify', BaseNvmIdentify)

class NvmIdentify1(BaseNvmIdentify):
    VERSION = 1

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify1)
    ]

    def __init__(self):
        super().__init__()

        self.hdr.version = self.VERSION
        self.hdr.length = sizeof(self.payload)

class NvmIdentify2(BaseNvmIdentify):
    VERSION = 2

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify2)
    ]

    @property
    def payload(self) -> Identify2:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify2):
        super().payload = value

class NvmIdentify3(BaseNvmIdentify):
    VERSION = 3

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify3)
    ]

    @property
    def payload(self) -> Identify3:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify3):
        super().payload = value

class NvmIdentify4(BaseNvmIdentify):
    VERSION = 4

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify4)
    ]

    @property
    def payload(self) -> Identify4:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify4):
        super().payload = value

class NvmIdentify5(BaseNvmIdentify):
    VERSION = 5

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify5)
    ]

    @property
    def payload(self) -> Identify5:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify5):
        super().payload = value

class NvmIdentify6(BaseNvmIdentify):
    VERSION = 6
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify6)
    ]

    @property
    def payload(self) -> Identify6:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify6):
        super().payload = value

class NvmIdentify7(BaseNvmIdentify):
    VERSION = 7
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify7)
    ]

    @property
    def payload(self) -> Identify7:
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value: Identify7):
        super().payload = value
