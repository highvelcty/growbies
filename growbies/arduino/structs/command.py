from enum import IntEnum
from typing import ByteString, cast, Optional, NewType, Type, TypeVar, Union
import ctypes
import logging

from growbies.utils.bufstr import BufStr
from growbies.utils.report import format_float_table

logger = logging.getLogger(__name__)

# --- Constants ------------------------------------------------------------------------------------
COEFFICIENT_COUNT = 2
TARE_COUNT = 1
MASS_SENSOR_COUNT = 1
TEMPERATURE_SENSOR_COUNT = 1

# --- Base Classes ---------------------------------------------------------------------------------
class Command(IntEnum):
    LOOPBACK = 0
    GET_EEPROM = 1
    SET_EEPROM = 2
    READ_DAC = 3
    READ_UNITS = 4
    SET_PHASE = 5

class Response(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4
    MULTI_DATA_POINT = 5
    GET_EEPROM = 6
    GET_TARE = 7
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
        elif packet.header.type == cls.MULTI_DATA_POINT:
            return RespMultiDataPoint.make_class(packet)
        elif packet.header.type == cls.GET_EEPROM:
            return RespGetEEPROM

        logger.error(f'Transport layer unrecognized response type: {packet.header.type}')
        return None

class Error(IntEnum):
    NONE = 0
    ERROR_CMD_DESERIALIZATION_BUFFER_UNDERFLOW = 1
    ERROR_UNRECOGNIZED_COMMAND = 2

class Phase(IntEnum):
    A = 0
    B = 1

# --- Base Classes ---------------------------------------------------------------------------------
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
    def type(self) -> Union[Command, Response]:
        return super().type.value

    @type.setter
    def type(self, value: [Command, Response]):
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
        self.type = Command.LOOPBACK


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


# --- Misc Structures # ----------------------------------------------------------------------------
class EEPROM(ctypes.Structure):
    class Field:
        MASS_COEFFICIENT = '_mass_coefficient'
        TEMPERATURE_COEFFICIENT = '_temperature_coefficient'
        TARE = '_tare'

    _pack_ = 1
    _fields_ = [
        (Field.MASS_COEFFICIENT, ctypes.c_float * MASS_SENSOR_COUNT * COEFFICIENT_COUNT),
        (Field.TEMPERATURE_COEFFICIENT,
         ctypes.c_float * TEMPERATURE_SENSOR_COUNT * COEFFICIENT_COUNT),
        (Field.TARE,
         ctypes.c_float * MASS_SENSOR_COUNT * TARE_COUNT)
    ]

    def set_sensor_data(self, field, sensor: int, *values):
        if field == self.Field.MASS_COEFFICIENT:
            base_values = self.mass_coefficient
        elif field == self.Field.TEMPERATURE_COEFFICIENT:
            base_values = self.temperature_coefficient
        elif field == self.Field.TARE:
            base_values = self.tare
        else:
            raise Exception('Invalid field type.')

        for idx, row in enumerate(base_values):
            row[sensor] = values[idx]

        if field == self.Field.MASS_COEFFICIENT:
            self.mass_coefficient = base_values
        elif field == self.Field.TEMPERATURE_COEFFICIENT:
            self.temperature_coefficient = base_values
        elif field == self.Field.TARE:
            self.tare = base_values

    @property
    def mass_coefficient(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.MASS_COEFFICIENT)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @mass_coefficient.setter
    def mass_coefficient(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.MASS_COEFFICIENT)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def temperature_coefficient(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.TEMPERATURE_COEFFICIENT)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @temperature_coefficient.setter
    def temperature_coefficient(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.TEMPERATURE_COEFFICIENT)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def tare(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.TARE)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @tare.setter
    def tare(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.TARE)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    def __str__(self):
        str_list = [
            'Mass Coefficient:',
            format_float_table(self.mass_coefficient,
                [f'Sensor %d' % idx for idx in range(len(self.mass_coefficient[0]))]),
            '',
            'Temperature Coefficient:',
            format_float_table(self.temperature_coefficient,
                [f'Sensor %d' % idx for idx in range(len(self.temperature_coefficient[0]))]),
            '',
            'Tare:',
            format_float_table(self.tare,
                               [f'Sensor %d' % idx for idx in
                                range(len(self.tare[0]))])
        ]
        return '\n'.join(str_list)


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


# --- Commands -------------------------------------------------------------------------------------
class CmdGetEEPRROM(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.GET_EEPROM
        super().__init__(*args, **kw)

class CmdSetEEPRROM(BaseCommand):
    class Field(BaseCommand.Field):
        EEPROM = '_eeprom'

    _fields_ = [
        (Field.EEPROM, EEPROM)

    ]

    @property
    def eeprom(self) -> EEPROM:
        return getattr(self, self.Field.EEPROM)

    @eeprom.setter
    def eeprom(self, eeprom: EEPROM):
        setattr(self, self.Field.EEPROM, eeprom)

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.SET_EEPROM
        super().__init__(*args, **kw)


class CmdGetTare(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.GET_TARE
        super().__init__(*args, **kw)

class CmdReadDAC(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.READ_DAC
        super().__init__(*args, **kw)


class CmdReadUnits(BaseCmdWithTimesParam):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.READ_UNITS
        super().__init__(*args, **kw)


class CmdSetPhase(BaseCommand):
    class Field(BaseCommand.Field):
        PHASE = '_phase'

    _fields_ = [
        (Field.PHASE, ctypes.c_uint16),
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.SET_PHASE
        super().__init__(*args, **kw)

    @property
    def phase(self) -> int:
        return getattr(self, self.Field.PHASE)

    @phase.setter
    def phase(self, value: int):
        setattr(self, self.Field.PHASE, value)


# --- Responses ------------------------------------------------------------------------------------
class RespVoid(BaseResponse):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.VOID
        super().__init__(*args, **kw)


class BaseRespWithData(BaseResponse):
    class Field(BaseResponse.Field):
        DATA = 'data'


class RespByte(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.BYTE
        super().__init__(*args, **kw)


class RespLong(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_int32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.LONG
        super().__init__(*args, **kw)


class RespFloat(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.FLOAT
        super().__init__(*args, **kw)


class RespDouble(BaseRespWithData):
    """Arduino uno has 4 byte double, the same as a float."""
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.DOUBLE
        super().__init__(*args, **kw)


class RespError(BaseResponse):
    class Field(BaseResponse.Field):
        ERROR = 'error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Response.ERROR
        super().__init__(*args, **kw)

    @property
    def error(self) -> Error:
        return super().error

    @error.setter
    def error(self, value: Error):
        super().error = value


class RespGetEEPROM(BaseResponse):
    class Field(BaseResponse.Field):
        EEPROM = '_eeprom'

    _pack_ = 1
    _fields_ = [
        (Field.EEPROM, EEPROM)
    ]

    @property
    def eeprom(self) -> EEPROM:
        return getattr(self, self.Field.EEPROM)


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

# --- Protected functions --------------------------------------------------------------------------
def _set_ctypes_2d_array(array, values: list[list[float]]):
    for row_idx, row in enumerate(values):
        for column_idx, value in enumerate(row):
            array[row_idx][column_idx] = value

def _get_ctypes_2d_array(array):
    return [list(array[idx]) for idx in range(len(array))]