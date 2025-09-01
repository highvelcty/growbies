from datetime import datetime
from enum import IntEnum
from packaging.version import Version
import ctypes

from growbies.utils import timestamp
from growbies.utils.types import Serial_t, ModelNumber_t

__all__ = ['BatteryType', 'DisplayType', 'LedType', 'FrameType', 'FootType', 'MassSensorType',
           'PcbaType', 'TemperatureSensorType', 'WirelessType', 'Identify1']

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


class NvmHeader(ctypes.Structure):
    class Field:
        MAGIC = '_magic'
        VERSION = '_version'

class Identify0(ctypes.Structure):
    class Field:
        HEADER = '_header'
        FIRMWARE_VERSION = '_firmware_version'

    _pack_ = 1
    _fields_ = [
        (Field.HEADER, NvmHeader),
        (Field.FIRMWARE_VERSION, ctypes.c_char * 32),
    ]

    @property
    def header(self) -> NvmHeader:
        return getattr(self, self.Field.HEADER)

    @header.setter
    def header(self, value: NvmHeader):
        setattr(self, self.Field.HEADER, value)

    @property
    def firmware_version(self) -> Version:
        return getattr(self, self.Field.FIRMWARE_VERSION)

    @firmware_version.setter
    def firmware_version(self, value: Version):
        setattr(self, self.Field.FIRMWARE_VERSION, str(value))

class Identify1(Identify0):
    class Field(Identify0.Field):
        SERIAL_NUMBER = '_serial_number'
        MODEL_NUMBER = '_model_number'
        MANUFACTURE_DATE = '_manufacture_date'
        MASS_SENSOR_COUNT = '_mass_sensor_count'
        MASS_SENSOR_TYPE = '_mass_sensor_type'
        TEMPERATURE_SENSOR_COUNT = '_temperature_sensor_count'
        TEMPERATURE_SENSOR_TYPE = '_temperature_sensor_type'
        ARCHITECTURE = '_architecture'
        PCBA = '_pcba'
        WIRELESS = '_wireless'
        BATTERY = '_battery'
        DISPLAY = '_display'
        LED = '_led'
        FRAME = '_frame'
        FOOT = '_foot'

    _pack_ = 1
    _fields_ = [
        (Field.SERIAL_NUMBER, ctypes.c_char * 64),
        (Field.MODEL_NUMBER, ctypes.c_char * 64),
        (Field.MANUFACTURE_DATE, ctypes.c_float),
        (Field.MASS_SENSOR_COUNT, ctypes.c_uint16),
        (Field.MASS_SENSOR_TYPE, ctypes.c_uint16),
        (Field.TEMPERATURE_SENSOR_COUNT, ctypes.c_uint16),
        (Field.TEMPERATURE_SENSOR_TYPE, ctypes.c_uint16),
        (Field.ARCHITECTURE, ctypes.c_uint16),
        (Field.PCBA, ctypes.c_uint16),
        (Field.BATTERY, ctypes.c_uint16),
        (Field.DISPLAY, ctypes.c_uint16),
        (Field.LED, ctypes.c_uint16),
        (Field.FRAME, ctypes.c_uint16),
        (Field.FOOT, ctypes.c_uint16),
    ]

    @property
    def serial_number(self) -> Serial_t:
        return getattr(self, self.Field.SERIAL_NUMBER)

    @serial_number.setter
    def serial_number(self, value: Serial_t):
        setattr(self, self.Field.SERIAL_NUMBER, value)

    @property
    def model_number(self) -> ModelNumber_t:
        return getattr(self, self.Field.MODEL_NUMBER)

    @model_number.setter
    def model_number(self, value: ModelNumber_t):
        setattr(self, self.Field.MODEL_NUMBER, value)

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
    def mass_sensor_type(self) -> MassSensorType:
        try:
            return MassSensorType(getattr(self, self.Field.MASS_SENSOR_TYPE))
        except ValueError:
            return MassSensorType.GENERIC

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
        try:
            return TemperatureSensorType(getattr(self, self.Field.TEMPERATURE_SENSOR_TYPE))
        except ValueError:
            return TemperatureSensorType.GENERIC

    @temperature_sensor_type.setter
    def temperature_sensor_type(self, value: TemperatureSensorType):
        setattr(self, self.Field.TEMPERATURE_SENSOR_TYPE, value)

    @property
    def pcba(self) -> PcbaType:
        return PcbaType(getattr(self, self.Field.PCBA))

    @pcba.setter
    def pcba(self, value: PcbaType):
        setattr(self, self.Field.PCBA, PcbaType(value))

    @property
    def wireless(self) -> WirelessType:
        return WirelessType(getattr(self, self.Field.WIRELESS))

    @wireless.setter
    def wireless(self, value: WirelessType):
        setattr(self, self.Field.WIRELESS, value)

    @property
    def battery(self) -> BatteryType:
        try:
            return BatteryType(getattr(self, self.Field.BATTERY))
        except ValueError:
            return BatteryType.GENERIC

    @battery.setter
    def battery(self, value: BatteryType):
        setattr(self, self.Field.BATTERY, value)

    @property
    def display(self) -> DisplayType:
        try:
            return DisplayType(getattr(self, self.Field.DISPLAY))
        except ValueError:
            return DisplayType.GENERIC

    @display.setter
    def display(self, value: DisplayType):
        setattr(self, self.Field.DISPLAY, value)

    @property
    def led(self) -> LedType:
        try:
            return LedType(getattr(self, self.Field.LED))
        except ValueError:
            return LedType.GENERIC

    @led.setter
    def led(self, value: LedType):
        setattr(self, self.Field.LED, value)

    @property
    def frame(self) -> FrameType:
        try:
            return FrameType(getattr(self, self.Field.FRAME))
        except ValueError:
            return FrameType.GENERIC

    @frame.setter
    def frame(self, value: FrameType):
        setattr(self, self.Field.FRAME, value)

    @property
    def foot(self) -> FootType:
        try:
            return FootType(getattr(self, self.Field.FOOT))
        except ValueError:
            return FootType.GENERIC

    @foot.setter
    def foot(self, value: FootType):
        setattr(self, self.Field.FOOT, value)