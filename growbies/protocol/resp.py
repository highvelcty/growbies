from enum import IntEnum
from typing import Optional
import ctypes
import logging

from .common import  BaseStructure, BaseUnion, PacketHdr, TBaseStructure
from .common.calibration import NvmCalibration
from .common.identify import (NvmIdentify1, NvmIdentify2, NvmIdentify3, NvmIdentify4,
                              NvmIdentify5, NvmIdentify6, NvmIdentify7)
from .common.log import DeviceLog
from .common.read import DataPoint
from .common.tare import NvmTare
from .common.thermal import ThermalDeviceState
from growbies.service.common import ServiceCmdError
from growbies.common.enum import DeviceErrorCode

logger = logging.getLogger(__name__)

class DeviceRespOp(IntEnum):
    VOID = 0
    DATAPOINT = 1
    CALIBRATION = 2
    IDENTIFY = 3
    TARE = 4
    LOG = 5
    THERMAL_STATE = 6
    ERROR = 0xFFFF

    def __str__(self):
        return self.name

    @classmethod
    def from_frame(cls, hdr: 'RespPacketHdr', resp: bytearray | memoryview) \
            -> Optional['TBaseStructure']:

        def _raise_version_error(hdr_):
            raise ServiceCmdError(f'Unsupported version {hdr_.version} for "{hdr_.type}.')
        try:
            if hdr.type == cls.VOID:
                if hdr.version >= 1:
                    return VoidDeviceResp.from_buffer(resp)
            elif hdr.type == cls.ERROR:
                if hdr.version >= 1:
                    return ErrorDeviceResp.from_buffer(resp)
            elif hdr.type == cls.CALIBRATION:
                if hdr.version >= 1:
                    return NvmCalibration.from_buffer(resp)
            elif hdr.type == cls.DATAPOINT:
                if hdr.version >= 1:
                    return DataPoint(resp)
            elif hdr.type == cls.IDENTIFY:
                if hdr.version == 1:
                    return NvmIdentify1.from_buffer(resp)
                elif hdr.version == 2:
                    return NvmIdentify2.from_buffer(resp)
                elif hdr.version == 3:
                    return NvmIdentify3.from_buffer(resp)
                elif hdr.version == 4:
                    return NvmIdentify4.from_buffer(resp)
                elif hdr.version == 5:
                    return NvmIdentify5.from_buffer(resp)
                elif hdr.version == 6:
                    return NvmIdentify6.from_buffer(resp)
                elif hdr.version >= 7:
                    return NvmIdentify7.from_buffer(resp)
            elif hdr.type == cls.LOG:
                if hdr.version >= 1:
                    return DeviceLog.from_buffer(resp)
            elif hdr.type == cls.TARE:
                if hdr.version >= 1:
                    return NvmTare.from_buffer(resp)
            elif hdr.type == cls.THERMAL_STATE:
                if hdr.version >= 1:
                    return ThermalDeviceState.from_buffer(resp)
            else:
                raise ServiceCmdError(f'Unrecognized response type: {hdr.type}')
            _raise_version_error(hdr)
        except ValueError as err:
            logger.exception(err, exc_info=True)
            raise ServiceCmdError(f'Packet deserialization exception for type "{hdr.type}". '
                                  f'{err}') from err

class RespPacketHdr(PacketHdr):
    @property
    def type(self) -> DeviceRespOp:
        return DeviceRespOp(super().type)

    @type.setter
    def type(self, value: DeviceRespOp):
        setattr(self, self.Field.TYPE, value)

TDeviceResp = BaseStructure | BaseUnion

class ErrorDeviceResp(BaseStructure):
    class Field(BaseStructure.Field):
        ERROR = '_error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    @property
    def error(self) -> DeviceErrorCode | int:
        val = getattr(self, self.Field.ERROR)
        try:
            return DeviceErrorCode(val)
        except ValueError:
            return val

    @error.setter
    def error(self, value: DeviceErrorCode):
        setattr(self, self.Field.ERROR, value)

class VoidDeviceResp(BaseStructure): pass

class DeviceError(Exception):
    def __init__(self, error: DeviceErrorCode):
        try:
            error_msg = f'DeviceError {error}"'
        except ValueError:
            error_msg = error
        super().__init__(error_msg)
