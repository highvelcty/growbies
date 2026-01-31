from enum import IntEnum
from typing import NewType
import ctypes
import logging

from .common import BaseStructure, PacketHdr
from .common.calibration import NvmCalibration
from .common.identify import (NvmIdentify1, NvmIdentify2, NvmIdentify3, NvmIdentify4,
                              NvmIdentify5, NvmIdentify6, NvmIdentify7)
from .common.tare import NvmTare

logger = logging.getLogger(__name__)

class DeviceCmdOp(IntEnum):
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


class BaseDeviceCmd(BaseStructure): pass
TDeviceCmd = NewType('TDeviceCmd', BaseDeviceCmd)

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
    OP = DeviceCmdOp.GET_CALIBRATION
    VERSION = 1

class ReadDeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.READ
    VERSION = 1

    def __init__(self, ref_mass: float | None, sensor_ref_mass: list[float] | None):
        super().__init__()
        self._ref_mass = ref_mass
        self._sensor_ref_mass = sensor_ref_mass

    @property
    def ref_mass(self) -> float | None:
        return self._ref_mass

    @property
    def sensor_ref_mass(self) -> list[float] | None:
        return self._sensor_ref_mass

class SetCalibrationDeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_CALIBRATION
    VERSION = 1

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        CALIBRATION = '_calibration'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.CALIBRATION, NvmCalibration)

    ]

    @property
    def calibration(self) -> NvmCalibration:
        return getattr(self, self.Field.CALIBRATION)

    @calibration.setter
    def calibration(self, calibration: NvmCalibration):
        setattr(self, self.Field.CALIBRATION, calibration)

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)


class GetIdentifyDeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.GET_IDENTIFY
    VERSION = 1

class SetIdentifyDeviceCmd1(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify1.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify1),
    ]

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)

    @property
    def identify(self) -> NvmIdentify1:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify1):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd2(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify2.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify2),
    ]

    @property
    def identify(self) -> NvmIdentify2:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify2):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd3(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify3.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify3),
    ]

    @property
    def identify(self) -> NvmIdentify3:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify3):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd4(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify4.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify4),
    ]

    @property
    def identify(self) -> NvmIdentify4:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify4):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd5(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify5.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify5),
    ]

    @property
    def identify(self) -> NvmIdentify5:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify5):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd6(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify6.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify6),
    ]

    @property
    def identify(self) -> NvmIdentify6:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify6):
        setattr(self, self.Field.IDENTIFY, val)

class SetIdentifyDeviceCmd7(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_IDENTIFY
    VERSION = NvmIdentify7.VERSION

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        IDENTIFY = '_identify'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.IDENTIFY, NvmIdentify7),
    ]

    @property
    def identify(self) -> NvmIdentify7:
        return getattr(self, self.Field.IDENTIFY)

    @identify.setter
    def identify(self, val: NvmIdentify7):
        setattr(self, self.Field.IDENTIFY, val)

class GetTareDeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.GET_TARE
    VERSION = 1

class SetTareDeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.SET_TARE
    VERSION = 2

    class Field(BaseDeviceCmd.Field):
        INIT = '_init'
        TARE = '_tare'

    _fields_ = [
        (Field.INIT, ctypes.c_bool),
        (Field.TARE, NvmTare),
    ]

    @property
    def init(self) -> bool:
        return getattr(self, self.Field.INIT)

    @init.setter
    def init(self, value: bool):
        setattr(self, self.Field.INIT, value)

    @property
    def tare(self) -> NvmTare:
        return getattr(self, self.Field.TARE)

    @tare.setter
    def tare(self, val: NvmTare):
        setattr(self, self.Field.TARE, val)

class PowerOffHx711DeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.POWER_OFF_HX711
    VERSION = 1


class PowerOnHx711DeviceCmd(BaseDeviceCmd):
    OP = DeviceCmdOp.POWER_ON_HX711
    VERSION = 1
