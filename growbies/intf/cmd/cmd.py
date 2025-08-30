from enum import IntEnum
from typing import Optional, TypeVar
import ctypes
import logging

from ..common import Calibration, PacketHeader, Identify

__all__ = ['DeviceCmd', 'BaseDeviceCmd', 'TDeviceCmd',
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
    def get_type(cls, cmd: 'TDeviceCmd') -> Optional['DeviceCmd']:
        if isinstance(cmd, LoopbackDeviceCmd):
            return DeviceCmd.LOOPBACK
        elif isinstance(cmd, GetDatapointDeviceCmd):
            return DeviceCmd.GET_CALIBRATION
        elif isinstance(cmd, SetCalibrationDeviceCmd):
            return DeviceCmd.SET_CALIBRATION
        elif isinstance(cmd, GetDatapointDeviceCmd):
            return DeviceCmd.GET_DATAPOINT
        elif isinstance(cmd, PowerOnHx711DeviceCmd):
            return DeviceCmd.POWER_ON_HX711
        elif isinstance(cmd, PowerOffHx711DeviceCmd):
            return DeviceCmd.POWER_OFF_HX711
        else:
            return None

class BaseDeviceCmd(PacketHeader):
    @property
    def type(self) -> DeviceCmd:
        return DeviceCmd(getattr(self, self.Field.TYPE))

    @type.setter
    def type(self, value: DeviceCmd):
        setattr(self, self.Field.TYPE, value)
TDeviceCmd = TypeVar('TDeviceCmd', bound=BaseDeviceCmd)

class BaseDeviceCmdWithTimesParam(BaseDeviceCmd):
    DEFAULT_TIMES = 7

    class Field(BaseDeviceCmd.Field):
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

class GetCalibrationDeviceCmd(BaseDeviceCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.GET_CALIBRATION
        super().__init__(*args, **kw)

class SetCalibrationDeviceCmd(BaseDeviceCmd):
    class Field(BaseDeviceCmd.Field):
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

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.SET_CALIBRATION
        super().__init__(*args, **kw)

class GetIdentifyDeviceCmd(BaseDeviceCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.GET_IDENTIFY
        super().__init__(*args, **kw)

class SetIdentifyDeviceCmd(BaseDeviceCmd):
    class Field(BaseDeviceCmd.Field):
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.IDENTIFY, Identify)

    ]

    @property
    def identify(self) -> Identify:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, identify: Identify):
        setattr(self, self.Field.IDENTIFY, identify)

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.SET_CALIBRATION
        super().__init__(*args, **kw)


class GetDatapointDeviceCmd(BaseDeviceCmdWithTimesParam):
    class Field(BaseDeviceCmdWithTimesParam.Field):
        RAW = '_raw'

    _fields_ = [
        (Field.RAW, ctypes.c_bool)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.GET_DATAPOINT
        super().__init__(*args, **kw)

    @property
    def raw(self) -> bool:
        return getattr(self, self.Field.RAW)

    @raw.setter
    def raw(self, val: bool):
        setattr(self, self.Field.RAW, val)

class LoopbackDeviceCmd(BaseDeviceCmd):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = DeviceCmd.LOOPBACK

class PowerOffHx711DeviceCmd(BaseDeviceCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.POWER_OFF_HX711
        super().__init__(*args, **kw)

class PowerOnHx711DeviceCmd(BaseDeviceCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = DeviceCmd.POWER_ON_HX711
        super().__init__(*args, **kw)