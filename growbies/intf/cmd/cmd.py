from enum import IntEnum
from typing import Optional, TypeVar
import ctypes
import logging

from ..common import Calibration, PacketHdr, Identify1, BaseStructure

__all__ = ['DeviceCmd', 'BaseDeviceCmd', 'TDeviceCmd',
           'CmdPacketHdr',
           'LoopbackDeviceCmd',
           'GetCalibrationDeviceCmd', 'SetCalibrationDeviceCmd',
           'GetIdentifyDeviceCmd', 'SetIdentifyDeviceCmd',
           'PowerOnHx711DeviceCmd', 'PowerOffHx711DeviceCmd', 'GetDatapointDeviceCmd']

logger = logging.getLogger(__name__)

class DeviceCmd(IntEnum):
    LOOPBACK = 0
    GET_CALIBRATION = 1
    SET_CALIBRATION = 2
    GET_DATAPOINT = 3
    POWER_ON_HX711 = 4
    POWER_OFF_HX711 = 5
    GET_IDENTIFY = 6
    SET_IDENTIFY = 7

    def __str__(self):
        return self.name

    @classmethod
    def get_hdr(cls, cmd: 'TDeviceCmd') -> Optional['CmdPacketHdr']:

        if isinstance(cmd, GetDatapointDeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.GET_CALIBRATION)
        elif isinstance(cmd, SetCalibrationDeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.SET_CALIBRATION)
        elif isinstance(cmd, GetDatapointDeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.GET_DATAPOINT)
        elif isinstance(cmd, GetIdentifyDeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.GET_IDENTIFY)
        elif isinstance(cmd, LoopbackDeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.LOOPBACK)
        elif isinstance(cmd, PowerOnHx711DeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.POWER_ON_HX711)
        elif isinstance(cmd, PowerOffHx711DeviceCmd):
            return CmdPacketHdr(type=DeviceCmd.POWER_OFF_HX711)
        else:
            logger.error(f'Unknown cmd type {type(cmd)}.')
            return None

class CmdPacketHdr(PacketHdr):
    @property
    def type(self) -> DeviceCmd | int:
        """Return :class:`DeviceCmd` if enumerated, integer otherwise."""
        try:
            return DeviceCmd(super().type)
        except ValueError:
            return super().type

    @type.setter
    def type(self, value: DeviceCmd):
        setattr(self, self.Field.TYPE, DeviceCmd(value))

class BaseDeviceCmd(BaseStructure): pass
TDeviceCmd = TypeVar('TDeviceCmd', bound=BaseDeviceCmd)

class BaseDeviceCmdWithTimesParam(BaseDeviceCmd):
    DEFAULT_TIMES = 7

    class Field:
        TIMES = '_times'

    _fields_ = [
        # How many samples to read from the HX711 per data point.
        (Field.TIMES, ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        kw.setdefault(self.Field.TIMES, self.DEFAULT_TIMES)
        super().__init__(*args, **kw)

    @property
    def times(self) -> int:
        return super().times

    @times.setter
    def times(self, value: int):
        super().times = value

class GetCalibrationDeviceCmd(BaseDeviceCmd): pass

class SetCalibrationDeviceCmd(BaseDeviceCmd):
    class Field:
        CALIBRATION = '_calibration'

    _fields_ = [
        (Field.CALIBRATION, Calibration)

    ]

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)

    @calibration.setter
    def calibration(self, calibration: Calibration):
        setattr(self, self.Field.CALIBRATION, calibration)

class GetIdentifyDeviceCmd(BaseDeviceCmd): pass

class SetIdentifyDeviceCmd(BaseDeviceCmd):
    class Field:
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.IDENTIFY, Identify1)
    ]

    @property
    def identify(self) -> Identify1:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, identify: Identify1):
        setattr(self, self.Field.IDENTIFY, identify)


class GetDatapointDeviceCmd(BaseDeviceCmdWithTimesParam):
    class Field(BaseDeviceCmdWithTimesParam.Field):
        RAW = '_raw'

    _fields_ = [
        (Field.RAW, ctypes.c_bool)
    ]

    @property
    def raw(self) -> bool:
        return getattr(self, self.Field.RAW)

    @raw.setter
    def raw(self, val: bool):
        setattr(self, self.Field.RAW, val)

class LoopbackDeviceCmd(BaseDeviceCmd): pass

class PowerOffHx711DeviceCmd(BaseDeviceCmd): pass

class PowerOnHx711DeviceCmd(BaseDeviceCmd): pass
