from enum import IntEnum
from typing import Optional
import ctypes
import logging

from .common import  BaseStructure, BaseUnion, PacketHdr, TBaseStructure
from .common.calibration import NvmCalibration
from .common.identify import (NvmIdentify1, NvmIdentify2, NvmIdentify3, NvmIdentify4,
                              NvmIdentify5, NvmIdentify6)
from .common.read import DataPoint
from .common.tare import NvmTare
from growbies.service.common import ServiceCmdError

logger = logging.getLogger(__name__)

class DeviceRespOp(IntEnum):
    VOID = 0
    DATAPOINT = 1
    CALIBRATION = 2
    IDENTIFY = 3
    TARE = 4
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
                    resp = VoidDeviceResp.from_buffer(resp)
                else:
                    _raise_version_error(hdr)
            elif hdr.type == cls.ERROR:
                if hdr.version >= 1:
                    resp = ErrorDeviceResp.from_buffer(resp)
                else:
                    _raise_version_error(hdr)
            elif hdr.type == cls.DATAPOINT:
                if hdr.version >= 1:
                    resp = DataPoint(resp)
                else:
                    _raise_version_error(hdr)
            elif hdr.type == cls.CALIBRATION:
                if hdr.version >= 1:
                    resp = NvmCalibration.from_buffer(resp)
                else:
                    _raise_version_error(hdr)
            elif hdr.type == cls.IDENTIFY:
                if hdr.version == 1:
                    resp = NvmIdentify1.from_buffer(resp)
                elif hdr.version == 2:
                    resp = NvmIdentify2.from_buffer(resp)
                elif hdr.version == 3:
                    resp = NvmIdentify3.from_buffer(resp)
                elif hdr.version == 4:
                    resp = NvmIdentify4.from_buffer(resp)
                elif hdr.version == 5:
                    resp = NvmIdentify5.from_buffer(resp)
                elif hdr.version >= 6:
                    resp = NvmIdentify6.from_buffer(resp)
                else:
                    _raise_version_error(hdr)
            elif hdr.type == cls.TARE:
                if hdr.version >= 1:
                    resp = NvmTare.from_buffer(resp)
                else:
                    _raise_version_error(hdr)
            else:
                raise ServiceCmdError(f'Unrecognized response type: {hdr.type}')
        except ValueError as err:
            logger.exception(err, exc_info=True)
            raise ServiceCmdError(f'Packet deserialization exception for type "{hdr.type}". '
                                  f'{err}') from err

        return resp

class DeviceErrorCode(IntEnum):
    # bitfield
    NONE                                  = 0x00000000
    CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001
    UNRECOGNIZED_COMMAND                  = 0x00000002
    OUT_OF_THRESHOLD_SAMPLE               = 0x00000004
    HX711_NOT_READY                       = 0x00000008
    INTERNAL                              = 0x00000010
    INVALID_PARAMETER                     = 0x00000020
    INCOMPLETE_SLIP_FRAME                 = 0x00000040
    INVALID_SLIP_CRC                      = 0x00000080
    CMD_HDR_DESERIALIZATION_UNDERFLOW     = 0x00000100

    def __str__(self):
        return self.name

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
        HDR = '_hdr'
        ERROR = '_error'

    _fields_ = [
        (Field.HDR, PacketHdr),
        (Field.ERROR, ctypes.c_uint32)
    ]

    @property
    def hdr(self) -> PacketHdr:
        return getattr(self, self.Field.HDR)

    @hdr.setter
    def hdr(self, value: PacketHdr):
        setattr(self, self.Field.HDR, value)

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
            error_msg = f'DeviceError 0x{error:08X} "{error}".'
        except ValueError:
            error_msg = error
        super().__init__(error_msg)
