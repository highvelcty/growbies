from abc import ABC, ABCMeta, abstractmethod
from enum import IntEnum
from typing import NewType
import ctypes
import logging

from .common import BaseStructure, PacketHdr
from .common.calibration import Calibration
from .common.identify import Identify1, TIdentify
from .common.tare import Tare

logger = logging.getLogger(__name__)

class DeviceCmdOp(IntEnum):
    LOOPBACK = 0
    GET_CALIBRATION = 1
    SET_CALIBRATION = 2
    GET_DATAPOINT = 3
    POWER_ON_HX711 = 4
    POWER_OFF_HX711 = 5
    GET_IDENTIFY = 6
    SET_IDENTIFY = 7
    GET_TARE = 8
    SET_TARE = 9
    READ = 10

    def __str__(self):
        return self.name


class CmdPacketHdr(PacketHdr):
    @property
    def type(self) -> DeviceCmdOp | int:
        """Return :class:`DeviceCmd` if enumerated, integer otherwise."""
        try:
            return DeviceCmdOp(super().type)
        except ValueError:
            return super().type

    @type.setter
    def type(self, value: DeviceCmdOp):
        setattr(self, self.Field.TYPE, DeviceCmdOp(value))


class ABCStructureMeta(type(BaseStructure), ABCMeta): pass

class BaseDeviceCmd(BaseStructure, metaclass=ABCStructureMeta):
    # problems following the metaclass inheritance with pycharm 2025.1.3.1
    # noinspection PyAbstractClass
    @classmethod
    @abstractmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        ...
TDeviceCmd = NewType('TDeviceCmd', BaseDeviceCmd)

class BaseDeviceCmdWithTimesParam(BaseDeviceCmd, ABC):
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
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.GET_CALIBRATION, 0

class ReadDeviceCmd(BaseDeviceCmd):
    DEFAULT_TIMES = 7

    class Field(BaseDeviceCmd.Field):
        TIMES = '_times'
        RAW = '_raw'

    _fields_ = [
        (Field.TIMES, ctypes.c_uint8),
        (Field.RAW, ctypes.c_bool)
    ]

    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.READ, 0

    @property
    def raw(self) -> bool:
        return getattr(self, self.Field.RAW)

    @raw.setter
    def raw(self, value: bool):
        setattr(self, self.Field.RAW, value)

    @property
    def times(self) -> int:
        return getattr(self, self.Field.TIMES)

    @times.setter
    def times(self, value: int):
        setattr(self, self.Field.TIMES, value)

class SetCalibrationDeviceCmd(BaseDeviceCmd):
    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        CALIBRATION = '_calibration'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.CALIBRATION, Calibration)

    ]

    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.SET_CALIBRATION, 0

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)

    @calibration.setter
    def calibration(self, calibration: Calibration):
        setattr(self, self.Field.CALIBRATION, calibration)

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)

class GetIdentifyDeviceCmd(BaseDeviceCmd):
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.GET_IDENTIFY, 0

class SetIdentifyDeviceCmd(BaseDeviceCmd):
    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, Identify1),
    ]

    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.SET_IDENTIFY, 1

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)

    @property
    def identify(self) -> TIdentify:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: TIdentify):
        setattr(self, self.Field.IDENTIFY, val)

class GetTareDeviceCmd(BaseDeviceCmd):
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.GET_TARE, 0

class SetTareDeviceCmd(BaseDeviceCmd):
    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        TARE = '_tare'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.TARE, Tare),
    ]

    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.SET_TARE, 0

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)

    @property
    def tare(self) -> Tare:
        return getattr(self, self.Field.TARE)

    @tare.setter
    def tare(self, val: Tare):
        setattr(self, self.Field.TARE, val)

class LoopbackDeviceCmd(BaseDeviceCmd):
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.LOOPBACK, 0


class PowerOffHx711DeviceCmd(BaseDeviceCmd):
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.POWER_OFF_HX711, 0


class PowerOnHx711DeviceCmd(BaseDeviceCmd):
    @classmethod
    def get_op_and_version(cls) -> tuple[DeviceCmdOp, int]:
        return DeviceCmdOp.POWER_ON_HX711, 0
