from enum import IntEnum
from typing import Optional
import ctypes
import logging

from .common import  BaseStructure, BaseUnion, PacketHdr, TBaseStructure
from .common.calibration import Calibration
from .common.identify import Identify, Identify1
from .common.read import DataPoint
from .common.tare import Tare

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
    def from_frame(cls, frame: bytearray | memoryview) \
            -> tuple[Optional['RespPacketHdr'], Optional['TBaseStructure']]:
        packet_hdr = None
        resp = None

        try:
            packet_hdr = RespPacketHdr.from_buffer(frame)
        except ValueError as err:
            logger.error(f'Packet header deserialization exception: {err}')
            return packet_hdr, resp
        try:
            if packet_hdr.type == cls.VOID:
                resp = VoidDeviceResp.from_buffer(frame, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.ERROR:
                resp = ErrorDeviceResp.from_buffer(frame, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.DATAPOINT:
                resp = DataPoint(frame[ctypes.sizeof(packet_hdr):])
            elif packet_hdr.type == cls.CALIBRATION:
                resp = (Calibration.from_buffer(frame, ctypes.sizeof(packet_hdr)))
            elif packet_hdr.type == cls.IDENTIFY:
                if packet_hdr.version == 0:
                    resp = Identify.from_buffer(frame, ctypes.sizeof(packet_hdr))
                elif packet_hdr.version == 1:
                    resp = Identify1.from_buffer(frame, ctypes.sizeof(packet_hdr))
                else:
                    logger.warning(f'Unimplemented identify version {packet_hdr.version}.')
                    resp = Identify1.from_buffer(frame, ctypes.sizeof(packet_hdr))
            elif packet_hdr.type == cls.TARE:
                resp = Tare.from_buffer(frame, ctypes.sizeof(packet_hdr))
            else:
                logger.error(f'Unrecognized response type: {packet_hdr.type}')
        except ValueError as err:
            logger.error(f'Packet deserialization exception for type "{packet_hdr.type}": {err}')

        return packet_hdr, resp


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
    def type(self) -> DeviceRespOp:
        return DeviceRespOp(super().type)

    @type.setter
    def type(self, value: DeviceRespOp):
        setattr(self, self.Field.TYPE, value)

TDeviceResp = BaseStructure | BaseUnion

class ErrorDeviceResp(BaseStructure):
    class Field(PacketHdr.Field):
        ERROR = '_error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    @property
    def error(self) -> DeviceErrorCode:
        return DeviceErrorCode(getattr(self, self.Field.ERROR))

    @error.setter
    def error(self, value: DeviceErrorCode):
        setattr(self, self.Field.ERROR, value)

class GetCalibrationDeviceResp(BaseStructure):
    class Field(BaseStructure.Field):
        CALIBRATION = '_calibration'

    _fields_ = [
        (Field.CALIBRATION, Calibration)
    ]

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)

    def __str__(self):
        return str(self.calibration)


class VoidDeviceResp(BaseStructure): pass


class DeviceError(Exception):
    def __init__(self, error: DeviceErrorCode):
        try:
            error_msg = f'DeviceError 0x{error:08X} "{error}".'
        except ValueError:
            error_msg = error
        super().__init__(error_msg)
