from enum import IntEnum
from typing import Optional, Type, TypeVar
import ctypes

from ..common import IdentifyPacket1, BaseStructure
from ..common import Calibration, Packet, PacketHeader
from ..common import MASS_SENSOR_COUNT, TEMPERATURE_SENSOR_COUNT

class DeviceResp(IntEnum):
    VOID = 0
    DATAPOINT = 1
    CALIBRATION = 2
    IDENTIFY = 3
    ERROR = 0xFFFF

    def __str__(self):
        return self.name

    @classmethod
    def get_class(cls, packet: 'Packet') -> Optional[Type['TDeviceResp']]:
        if packet.hdr.type == cls.VOID:
            return VoidDeviceResp
        elif packet.hdr.type == cls.ERROR:
            return ErrorDeviceResp
        elif packet.hdr.type == cls.DATAPOINT:
            return DataPointDeviceResp
        elif packet.hdr.type == cls.CALIBRATION:
            return GetCalibrationDeviceRespGetCalibration
        elif packet.hdr.type == cls.IDENTIFY:
            return GetIdentifyDeviceResp
        else:
            return None


error_t = ctypes.c_uint32
class DeviceErrorCode(IntEnum):
    # bitfield
    NONE                                  = 0x00000000
    CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001
    UNRECOGNIZED_COMMAND                  = 0x00000002
    OUT_OF_THRESHOLD_SAMPLE               = 0x00000004
    HX711_NOT_READY                       = 0x00000008

    def __str__(self):
        return self.name

class RespPacketHeader(PacketHeader):
    @property
    def type(self) -> DeviceResp:
        return DeviceResp(super().type)

    @type.setter
    def type(self, value: DeviceResp):
        setattr(self, self.Field.TYPE, value)


class BaseDeviceResp(BaseStructure):
    class Field:
        HDR = '_hdr'

    _fields_ = [
        (Field.HDR, RespPacketHeader)
    ]

    @property
    def hdr(self) -> RespPacketHeader:
        return getattr(self, self.Field.HDR)
TDeviceResp = TypeVar('TDeviceResp', bound=BaseDeviceResp)

class ErrorDeviceResp(BaseDeviceResp):
    class Field(PacketHeader.Field):
        ERROR = 'error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    @property
    def error(self) -> DeviceErrorCode:
        return super().error

    @error.setter
    def error(self, value: DeviceErrorCode):
        super().error = value


class DataPointDeviceResp(BaseDeviceResp):
    class Field(BaseDeviceResp.Field):
        MASS_SENSOR = '_mass_sensor'
        MASS = '_mass'
        TEMPERATURE_SENSOR = '_temperature_sensor'
        TEMPERATURE = '_temperature'

    _pack_ = 1
    _fields_ = [
        (Field.MASS_SENSOR, ctypes.c_float * MASS_SENSOR_COUNT),
        (Field.MASS, ctypes.c_float),
        (Field.TEMPERATURE_SENSOR, ctypes.c_float * TEMPERATURE_SENSOR_COUNT),
        (Field.TEMPERATURE, ctypes.c_float)
    ]

    @property
    def mass_sensor(self) -> list[float]:
        return list(getattr(self, self.Field.MASS_SENSOR))

    @property
    def mass(self) -> float:
        return getattr(self, self.Field.MASS)

    @property
    def temperature_sensor(self) -> list[float]:
        return list(getattr(self, self.Field.TEMPERATURE_SENSOR))

    @property
    def temperature(self) -> float:
        return getattr(self, self.Field.TEMPERATURE)

    def __str__(self):
        str_list = list()
        for idx, val in enumerate(self.mass_sensor):
            str_list.append(f'mass_sensor_{idx}: {val}')
        str_list.append(f'mass: {self.mass}')
        str_list.append('')
        for idx, val in enumerate(self.temperature_sensor):
            str_list.append(f'temperature_sensor_{idx}: {val}')
        str_list.append(f'temperature: {self.temperature}')
        return '\n'.join(str_list)

class GetCalibrationDeviceRespGetCalibration(BaseDeviceResp):
    class Field(BaseDeviceResp.Field):
        CALIBRATION = '_calibration'

    _pack_ = 1
    _fields_ = [
        (Field.CALIBRATION, Calibration)
    ]

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)

class GetIdentifyDeviceResp(BaseDeviceResp):
    class Field(BaseDeviceResp.Field):
        ID = '_id'

    _pack_ = 1
    _fields_ =  [
        (Field.ID, IdentifyPacket1)
    ]

    @property
    def id(self) -> IdentifyPacket1:
        return getattr(self, self.Field.ID)

class VoidDeviceResp(BaseDeviceResp): pass


class DeviceError(Exception):
    def __init__(self, error: DeviceErrorCode):
        self.error = error
        super().__init__(f'DeviceError 0x{error:08X} "{error}".')
