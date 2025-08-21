from enum import IntEnum
from typing import TypeVar
import ctypes
import logging

from ..common import Calibration, PacketHeader

__all__ = ['Cmd', 'BaseCmd', 'TBaseCmd',
           'CmdLoopback', 'CmdGetCalibration', 'CmdSetCalibration', 'CmdPowerOnHx711',
           'CmdPowerOffHx711', 'CmdGetDatapoint']

logger = logging.getLogger(__name__)

class Cmd(IntEnum):
    LOOPBACK = 0
    GET_CALIBRATION = 1
    SET_CALIBRATION = 2
    GET_DATAPOINT = 3
    POWER_ON_HX711 = 4
    POWER_OFF_HX711 = 5

    def __str__(self):
        return self.name

class BaseCmd(PacketHeader):
    @property
    def type(self) -> Cmd:
        return Cmd(getattr(self, self.Field.TYPE))

    @type.setter
    def type(self, value: Cmd):
        setattr(self, self.Field.TYPE, value)
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)

class BaseCmdWithTimesParam(BaseCmd):
    DEFAULT_TIMES = 7

    class Field(BaseCmd.Field):
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

class CmdLoopback(BaseCmd):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Cmd.LOOPBACK


class CmdGetCalibration(BaseCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.GET_CALIBRATION
        super().__init__(*args, **kw)

class CmdSetCalibration(BaseCmd):
    class Field(BaseCmd.Field):
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
        kw[self.Field.TYPE] = Cmd.SET_CALIBRATION
        super().__init__(*args, **kw)

class CmdPowerOnHx711(BaseCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.POWER_ON_HX711
        super().__init__(*args, **kw)

class CmdPowerOffHx711(BaseCmd):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.POWER_OFF_HX711
        super().__init__(*args, **kw)

class CmdGetDatapoint(BaseCmdWithTimesParam):
    class Field(BaseCmdWithTimesParam.Field):
        RAW = '_raw'

    _fields_ = [
        (Field.RAW, ctypes.c_bool)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.GET_DATAPOINT
        super().__init__(*args, **kw)

    @property
    def raw(self) -> bool:
        return getattr(self, self.Field.RAW)

    @raw.setter
    def raw(self, val: bool):
        setattr(self, self.Field.RAW, val)