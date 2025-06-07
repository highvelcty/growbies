from enum import IntEnum
from typing import ByteString, cast, Optional, Type, TypeVar, Union
import ctypes
import logging

from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)


class CmdType(IntEnum):
    LOOPBACK = 0
    READ_MEDIAN_FILTER_AVG = 1
    SET_GAIN = 2
    GET_VALUE = 3
    GET_UNITS = 4
    TARE = 5
    SET_SCALE = 6
    GET_SCALE = 7
    SET_OFFSET = 8
    GET_OFFSET = 9
    POWER_DOWN = 10
    POWER_UP = 11


class RespType(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4
    MASS_DATA_POINT = 5
    ERROR = 0xFFFF

    @classmethod
    def get_struct(cls, packet: 'Packet') -> Optional[Type['TBaseResponse']]:
        if packet.header.type == cls.VOID:
            return RespVoid
        elif packet.header.type == cls.BYTE:
            return RespByte
        elif packet.header.type == cls.LONG:
            return RespLong
        elif packet.header.type == cls.FLOAT:
            return RespFloat
        elif packet.header.type == cls.DOUBLE:
            return RespDouble
        elif packet.header.type == cls.ERROR:
            return RespError
        elif packet.header.type == cls.MASS_DATA_POINT:
            return RespMassDataPoint.make_class(packet)

        logger.error(f'Transport layer unrecognized response type: {packet.header.type}')


class Error(IntEnum):
    NONE = 0
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1
    ERROR_UNRECOGNIZED_COMMAND = 2
    ERROR_HX711_NOT_READY = 3


class Gain(IntEnum):
    GAIN_32 = 32
    GAIN_64 = 64
    GAIN_128 = 128


class BaseStructure(ctypes.Structure):
    @classmethod
    def qualname(cls):
        return cls.__qualname__

    def __str__(self):
        return str(BufStr(memoryview(self).cast('B'),
                          title=self.qualname()))
TBaseStructure = TypeVar('TBaseStructure', bound=BaseStructure)


class BasePacket(BaseStructure):
    @classmethod
    def from_packet(cls, packet: 'Packet') -> Optional['TBasePacket']:
        return cls.from_buffer(packet)
TBasePacket = TypeVar('TBasePacket', bound=BasePacket)


class PacketHeader(BaseStructure):
    class Field:
        TYPE = 'type'

    _pack_ = 1
    _fields_ = [
        (Field.TYPE, ctypes.c_uint16),
    ]

    @property
    def type(self) -> Union[CmdType, RespType]:
        return super().type.value

    @type.setter
    def type(self, value: [CmdType, RespType]):
        super().type = value


class Packet(BasePacket):
    MIN_SIZE_IN_BYTES = ctypes.sizeof(PacketHeader)

    class Field:
        HEADER = 'header'
        DATA = 'data'

    @classmethod
    def make(cls, source: Union[ByteString, int]) -> Optional['Packet']:
        if isinstance(source, int):
            source = bytearray(source)
        buf_len = len(source)
        data_len = buf_len - cls.MIN_SIZE_IN_BYTES
        class _Packet(Packet):
            _pack_ = 1
            _fields_ = [
                (cls.Field.HEADER, PacketHeader),
                (cls.Field.DATA, ctypes.c_uint8 * data_len) # noqa - false positive pycharm 2025
            ]


        if buf_len < Packet.MIN_SIZE_IN_BYTES:
            logger.error(f'Buffer underflow for deserializing to {Packet.__class__}. '
                         f'Expected at least {Packet.MIN_SIZE_IN_BYTES} bytes, '
                         f'observed {buf_len} bytes.')
            return None

        packet = _Packet.from_buffer(cast(bytes, source))

        return packet

    @property
    def header(self) -> PacketHeader:
        return getattr(self, self.Field.HEADER)

    @property
    def data(self) -> ctypes.Array[ctypes.c_uint8]:
        return getattr(self, self.Field.DATA)


class BaseCommand(PacketHeader):
    pass
TBaseCommand = TypeVar('TBaseCommand', bound=BaseCommand)


class BaseResponse(PacketHeader):
    pass
TBaseResponse = TypeVar('TBaseResponse', bound=BaseResponse)


class CmdLoopback(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = CmdType.LOOPBACK


class BaseCmdWithTimesParam(BaseCommand):
    DEFAULT_TIMES = 7

    class Field(BaseCommand.Field):
        TIMES = 'times'

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


class CmdReadMedianFilterAvg(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.READ_MEDIAN_FILTER_AVG
        super().__init__(*args, **kw)


class CmdSetGain(BaseCommand):
    class Gain(IntEnum):
        GAIN_32 = 32
        GAIN_64 = 64
        GAIN_128 = 128
    DEFAULT_GAIN = Gain.GAIN_128

    class Field(BaseCommand.Field):
        GAIN = 'gain'

    _fields_ = [
        (Field.GAIN, ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.SET_GAIN
        kw.setdefault(self.Field.GAIN, self.DEFAULT_GAIN)
        super().__init__(*args, **kw)

    @property
    def gain(self) -> int:
        return super().gain

    @gain.setter
    def gain(self, value: int):
        super().gain = value


class CmdGetValue(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_VALUE
        super().__init__(*args, **kw)


class CmdGetUnits(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_UNITS
        super().__init__(*args, **kw)


class CmdTare(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.TARE
        super().__init__(*args, **kw)


class CmdSetScale(BaseCommand):
    DEFAULT_SCALE = 1.0

    class Field(BaseCommand.Field):
        SCALE = 'scale'

    _fields_ = [
        (Field.SCALE, ctypes.c_float)
    ]

    @property
    def scale(self) -> float:
        return super().scale

    @scale.setter
    def scale(self, value: float):
        super().scale = value

    def  __init__(self, *args, **kw):
        kw.setdefault(self.Field.SCALE, self.DEFAULT_SCALE)
        kw[self.Field.TYPE] = CmdType.SET_SCALE
        super().__init__(*args, **kw)


class CmdGetScale(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_SCALE
        super().__init__(*args, **kw)


class CmdSetOffset(BaseCommand):
    DEFAULT_OFFSET = 0

    class Field(BaseCommand.Field):
        OFFSET = 'offset'

    _fields_ = [
        # A "long" in arduino uno is the same as a signed 32-bit integer
        (Field.OFFSET, ctypes.c_int32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.SET_OFFSET
        kw.setdefault(self.Field.OFFSET, self.DEFAULT_OFFSET)
        super().__init__(*args, **kw)

    @property
    def offset(self) -> int:
        return super().offset

    @offset.setter
    def offset(self, value: int):
        super().offset = value


class CmdGetOffset(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_OFFSET
        super().__init__(*args, **kw)


class CmdPowerDown(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.POWER_DOWN
        super().__init__(*args, **kw)


class CmdPowerUp(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.POWER_UP
        super().__init__(*args, **kw)


class RespVoid(BaseResponse):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.VOID
        super().__init__(*args, **kw)


class BaseRespWithData(BaseResponse):
    class Field(BaseResponse.Field):
        DATA = 'data'


class RespByte(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.BYTE
        super().__init__(*args, **kw)


class RespLong(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_int32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.LONG
        super().__init__(*args, **kw)


class RespFloat(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.FLOAT
        super().__init__(*args, **kw)


class RespDouble(BaseRespWithData):
    """Arduino uno has 4 byte double, the same as a float."""
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.DOUBLE
        super().__init__(*args, **kw)


class RespError(BaseResponse):
    class Field(BaseResponse.Field):
        ERROR = 'error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = RespType.ERROR
        super().__init__(*args, **kw)

    @property
    def error(self) -> Error:
        return super().error

    @error.setter
    def error(self, value: Error):
        super().error = value


class MassDataPoint(ctypes.Structure):
    class Field(BaseResponse.Field):
        DATA = 'data'
        ERROR_COUNT = 'error_count'
        READY = 'ready'
        RESERVED1 = 'reserved1'
        RESERVED2 = 'reserved2'

    _pack_ = 1
    _fields_ = [
        (Field.DATA, ctypes.c_int32),
        (Field.ERROR_COUNT, ctypes.c_uint8),
        (Field.READY, ctypes.c_uint8, 1),
        (Field.RESERVED1, ctypes.c_uint8, 7),
        (Field.RESERVED2, ctypes.c_uint16),
    ]

    @property
    def data(self) -> int:
        return self[self.Field.DATA]


class RespMassDataPoint(BaseResponse):
    class Field(BaseResponse.Field):
        SENSOR = 'sensor'

    @classmethod
    def make_class(cls, packet: 'Packet') -> Type['RespMassDataPoint']:
        class _RespMassDataPoint(RespMassDataPoint):
            _num_sensors = (len(packet.data) // ctypes.sizeof(MassDataPoint))
            _fields_ = [
                (cls.Field.SENSOR, MassDataPoint * _num_sensors),
            ]
            _pack_ = 1


            @classmethod
            def qualname(cls):
                return f'{RespMassDataPoint.__qualname__} ({cls._num_sensors}x sensors):'

        return _RespMassDataPoint


    @classmethod
    def from_packet(cls, packet) -> Optional['RespMassDataPoint']:
        return cls.make_class(packet).from_buffer(packet)
