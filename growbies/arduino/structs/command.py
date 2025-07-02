from enum import IntEnum
from typing import ByteString, cast, Optional, Type, TypeVar, Union
import ctypes
import logging

from growbies import constants
from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)

MAX_NUMBER_OF_MASS_SENSORS = 5
C_FLOAT_MAX = 3.4028234663852886e+38
COEFFICIENT_COUNT = 2

class CmdType(IntEnum):
    LOOPBACK = 0
    READ_DAC = 1
    READ_UNITS = 2
    GET_SCALE = 3
    SET_SCALE = 4
    GET_TARE = 5
    SET_TARE = 6
    SET_PHASE = 7
    GET_TEMPERATURE_COEFFICIENT = 8
    SET_TEMPERATURE_COEFFICIENT = 9

class RespType(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4
    MASS_DATA_POINT = 5
    GET_TARE = 6
    GET_TEMPERATURE_COEFFICIENT = 7
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
            return RespMultiDataPoint.make_class(packet)
        elif packet.header.type == cls.GET_TARE:
            return RespGetTare
        elif packet.header.type == cls.GET_TEMPERATURE_COEFFICIENT:
            return RespGetTemperatureCoefficient

        logger.error(f'Transport layer unrecognized response type: {packet.header.type}')
        return None

class Error(IntEnum):
    NONE = 0
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1
    ERROR_UNRECOGNIZED_COMMAND = 2

class Phase(IntEnum):
    A = 0
    B = 1

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


class CmdReadDAC(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.READ_DAC
        super().__init__(*args, **kw)

class CmdReadUnits(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.READ_UNITS
        super().__init__(*args, **kw)

class CmdSetPhase(BaseCommand):
    class Field(BaseCommand.Field):
        PHASE = '_phase'

    _fields_ = [
        (Field.PHASE, ctypes.c_uint16),
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.SET_PHASE
        super().__init__(*args, **kw)

    @property
    def phase(self) -> int:
        return getattr(self, self.Field.PHASE)

    @phase.setter
    def phase(self, value: int):
        setattr(self, self.Field.PHASE, value)

class CmdGetTare(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_TARE
        super().__init__(*args, **kw)

class CmdGetScale(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_SCALE
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


class CmdSetTare(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.SET_TARE
        super().__init__(*args, **kw)

class CmdGetTemperatureCoefficient(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.GET_TEMPERATURE_COEFFICIENT
        super().__init__(*args, **kw)

class CmdSetTemperatureCoefficient(BaseCommand):
    class Field(BaseCommand.Field):
        COEFFICIENT = '_coefficient'

    _fields_ = [
        (Field.COEFFICIENT, ctypes.c_float * COEFFICIENT_COUNT)
    ]

    @property
    def coefficient(self) -> list[float]:
        return [getattr(self, self.Field.COEFFICIENT)[idx] for idx in range(COEFFICIENT_COUNT)]

    @coefficient.setter
    def coefficient(self, values: list[float]):
        for idx, value in enumerate(values):
            getattr(self, self.Field.COEFFICIENT)[idx] = value

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = CmdType.SET_TEMPERATURE_COEFFICIENT
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


class RespGetTare(BaseResponse):
    class Field(BaseResponse.Field):
        MASS_OFFSET = '_mass_offset'

    _pack_ = 1
    _fields_ = [
        (Field.MASS_OFFSET, ctypes.c_float * MAX_NUMBER_OF_MASS_SENSORS),
    ]

    @property
    def mass_offset(self) -> list[float]:
        return [offset for offset in getattr(self, self.Field.MASS_OFFSET) if offset !=
                C_FLOAT_MAX]

class RespGetTemperatureCoefficient(BaseResponse):
    class Field(BaseResponse.Field):
        COEFFICIENT = '_coefficient'

    _pack_ = 1
    _fields_ = [
        (Field.COEFFICIENT, ctypes.c_float * COEFFICIENT_COUNT),
    ]

    @property
    def coefficient(self) -> list[float]:
        return list(getattr(self, self.Field.COEFFICIENT))


class DataPoint(ctypes.Structure):
    class Field(BaseResponse.Field):
        DATA = '_data'
        ERROR_COUNT = '_error_count'
        READY = '_ready'
        RESERVED1 = 'reserved1'
        RESERVED2 = 'reserved2'

    _pack_ = 1
    _fields_ = [
        (Field.DATA, ctypes.c_float),
        (Field.ERROR_COUNT, ctypes.c_uint8),
        (Field.READY, ctypes.c_uint8, 1),
        (Field.RESERVED1, ctypes.c_uint8, 7),
        (Field.RESERVED2, ctypes.c_uint16),
    ]

    @property
    def data(self) -> float:
        return getattr(self, self.Field.DATA)

    @property
    def error_count(self) -> int:
        return getattr(self, self.Field.ERROR_COUNT)

    @property
    def ready(self) -> bool:
        return getattr(self, self.Field.READY)


class MultiDataPoint(ctypes.Structure):
    class Field(BaseResponse.Field):
        MASS = '_mass'
        TEMPERATURE = '_temperature'

    _pack_ = 1
    _fields_ = [
        (Field.MASS, DataPoint),
        (Field.TEMPERATURE, DataPoint),
    ]
    @property
    def mass(self) -> DataPoint:
        return getattr(self, self.Field.MASS)

    @property
    def temperature(self) -> DataPoint:
        return getattr(self, self.Field.TEMPERATURE)

    def __str__(self):
        str_list = list()
        for key, _ in self._fields_:
            str_list.append(f'{key}: {getattr(self, key).data}')
        return '\n'.join(str_list)


class RespMultiDataPoint(BaseResponse):
    class Field(BaseResponse.Field):
        SENSOR = 'sensor'

    @classmethod
    def make_class(cls, packet: 'Packet') -> Type['RespMultiDataPoint']:
        class _RespMassDataPoint(RespMultiDataPoint):
            _num_sensors = (len(packet.data) // ctypes.sizeof(MultiDataPoint))
            _fields_ = [
                (cls.Field.SENSOR, MultiDataPoint * _num_sensors),
            ]
            _pack_ = 1


            @classmethod
            def qualname(cls):
                return f'{RespMultiDataPoint.__qualname__} ({cls._num_sensors}x sensors):'

            def __str__(self):
                str_list = []
                for sensor in range(self._num_sensors):
                    str_list.append(str(getattr(self, self.Field.SENSOR)[sensor]))
                return '\n'.join(str_list)

        return _RespMassDataPoint


    @classmethod
    def from_packet(cls, packet) -> Optional['RespMultiDataPoint']:
        return cls.make_class(packet).from_buffer(packet)
