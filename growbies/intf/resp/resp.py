from enum import IntEnum
from typing import Optional, TypeVar
import ctypes
import logging

from ..common import  Identify0, Identify1, BaseStructure, NvmHeader
from ..common import Calibration, PacketHdr
from ..common import MASS_SENSOR_COUNT, TEMPERATURE_SENSOR_COUNT

logger = logging.getLogger(__name__)

class DeviceResp(IntEnum):
    VOID = 0
    DATAPOINT = 1
    CALIBRATION = 2
    IDENTIFY = 3
    ERROR = 0xFFFF

    def __str__(self):
        return self.name

    @classmethod
    def from_hdr(cls, packet_hdr: PacketHdr) -> Optional['TDeviceResp']:
        try:
            if packet_hdr.type == cls.VOID:
                return VoidDeviceResp.from_buffer(packet_hdr, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.ERROR:
                return ErrorDeviceResp.from_buffer(packet_hdr, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.DATAPOINT:
                return DataPointDeviceResp.from_buffer(packet_hdr, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.CALIBRATION:
                return (GetCalibrationDeviceRespGetCalibration
                        .from_buffer(packet_hdr, ctypes.sizeof(packet_hdr)))
            elif packet_hdr.type == cls.IDENTIFY:
                nvm_hdr = NvmHeader.from_buffer(packet_hdr, ctypes.sizeof(packet_hdr))
                if nvm_hdr.version == 0:
                    return (Identify0.
                            from_buffer(packet_hdr,
                                        ctypes.sizeof(packet_hdr) + ctypes.sizeof(nvm_hdr)))
                elif nvm_hdr.version == 1:
                    return (Identify1.
                            from_buffer(packet_hdr,
                                        ctypes.sizeof(packet_hdr) + ctypes.sizeof(nvm_hdr)))
                else:
                    logger.warning(f'Unimplemented identify version {nvm_hdr.version}.')
                    return (Identify1.
                            from_buffer(packet_hdr,
                                        ctypes.sizeof(packet_hdr) + ctypes.sizeof(nvm_hdr)))
            else:
                logger.error(f'Unrecognized response type: {packet_hdr.type}')
                return None
        except ValueError as err:
            logger.error(f'Packet deserialization exception for type "{packet_hdr.type}": {err}')
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

class RespPacketHdr(PacketHdr):
    @property
    def type(self) -> DeviceResp:
        return DeviceResp(super().type)

    @type.setter
    def type(self, value: DeviceResp):
        setattr(self, self.Field.TYPE, value)


class BaseDeviceResp(BaseStructure): pass
TDeviceResp = TypeVar('TDeviceResp', bound=BaseDeviceResp)

class ErrorDeviceResp(BaseDeviceResp):
    class Field(PacketHdr.Field):
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
    class Field:
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
    class Field:
        CALIBRATION = '_calibration'

    _pack_ = 1
    _fields_ = [
        (Field.CALIBRATION, Calibration)
    ]

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)


class VoidDeviceResp(BaseDeviceResp): pass


class DeviceError(Exception):
    def __init__(self, error: DeviceErrorCode):
        self.error = error
        super().__init__(f'DeviceError 0x{error:08X} "{error}".')
