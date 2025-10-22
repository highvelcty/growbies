from ctypes import sizeof
from datetime import datetime
from enum import IntEnum
from typing import Optional
import ctypes

from packaging.version import InvalidVersion, Version

from . import nvm
from .common import BaseStructure
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
    def serial_number(self) -> Optional[Serial_t]:
        return None

    @serial_number.setter
    def serial_number(self, value: Serial_t):
        pass

    @property
    def model_number(self) -> Optional[ModelNumber_t]:
        return None

    @model_number.setter
    def model_number(self, value: ModelNumber_t):
        pass

    @property
    def manufacture_date(self) -> Optional[datetime]:
        return None

    @manufacture_date.setter
    def manufacture_date(self, value: datetime):
        pass

    @property
    def mass_sensor_count(self) -> Optional[int]:
        return None

    @mass_sensor_count.setter
    def mass_sensor_count(self, value: int):
        pass

    @property
    def mass_sensor_type(self) -> Optional[MassSensorType]:
        return None

    @mass_sensor_type.setter
    def mass_sensor_type(self, value: MassSensorType):
        pass

    @property
    def temperature_sensor_count(self) -> Optional[int]:
        return None

    @temperature_sensor_count.setter
    def temperature_sensor_count(self, value: int):
        pass

    @property
    def temperature_sensor_type(self) -> Optional[TemperatureSensorType]:
        return None

    @temperature_sensor_type.setter
    def temperature_sensor_type(self, value: TemperatureSensorType):
        pass

    @property
    def pcba(self) -> Optional[PcbaType]:
        return None

    @pcba.setter
    def pcba(self, value: PcbaType):
        pass

    @property
    def wireless(self) -> Optional[WirelessType]:
        return None

    @wireless.setter
    def wireless(self, value: WirelessType):
        pass

    @property
    def battery(self) -> Optional[BatteryType]:
        return None

    @battery.setter
    def battery(self, value: BatteryType):
        pass

    @property
    def display(self) -> Optional[DisplayType]:
        return None

    @display.setter
    def display(self, value: DisplayType):
        pass

    @property
    def led(self) -> Optional[LedType]:
        return None

    @led.setter
    def led(self, value: LedType):
        pass

    @property
    def frame(self) -> Optional[FrameType]:
        return None

    @frame.setter
    def frame(self, value: FrameType):
        pass

    @property
    def foot(self) -> Optional[FootType]:
        return None

    @foot.setter
    def foot(self, value: FootType):
        pass

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

class NvmIdentify(nvm.BaseNvm):
    VERSION = 1

    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Identify1)
    ]

    def __init__(self):
        super().__init__()

        self.hdr.version = self.VERSION
        self.hdr.length = sizeof(self.payload)

    @property
    def payload(self) -> Identify1:
        return super().payload

    @payload.setter
    def payload(self, value: Identify1):
        super().payload = value
