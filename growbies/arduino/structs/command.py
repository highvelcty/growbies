from enum import IntEnum
from typing import Optional, Type, TypeVar
import ctypes
import logging

from .packet import PacketHeader

logger = logging.getLogger(__name__)


class Cmd(IntEnum):
    LOOPBACK = 0
    SAMPLE = 1


class RespType(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4

    @classmethod
    def get_struct(cls, type_: 'RespType') -> Optional[Type['TBaseResponse']]:
        if type_ == cls.VOID:
            return RespVoid
        elif type_ == cls.BYTE:
            return RespByte
        elif type_ == cls.LONG:
            return RespLong
        elif type_ == cls.FLOAT:
            return RespFloat
        elif type_ == cls.DOUBLE:
            return RespDouble


class BaseCommand(PacketHeader):
    pass
TBaseCommand = TypeVar('TBaseCommand', bound=BaseCommand)


class BaseResponse(PacketHeader):
    pass
TBaseResponse = TypeVar('TBaseResponse', bound=BaseResponse)


class CmdLoopback(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Cmd.LOOPBACK


class CmdSample(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Cmd.SAMPLE


class RespVoid(BaseResponse):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = RespType.VOID


class RespByte(BaseResponse):
    _fields_ = [
        ('data', ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = RespType.BYTE


class RespLong(BaseResponse):
    _fields_ = [
        ('data', ctypes.c_int32)
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = RespType.LONG


class RespFloat(BaseResponse):
    _fields_ = [
        ('data', ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = RespType.FLOAT


class RespDouble(BaseResponse):
    """Arduino uno has 4 byte double, the same as a float."""
    _fields_ = [
        ('data', ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = RespType.DOUBLE
