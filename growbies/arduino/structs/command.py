from enum import IntEnum
from typing import ByteString, cast, Optional, NewType, Type, TypeVar, Union
import ctypes
import logging

from growbies.utils.bufstr import BufStr
from growbies.utils.report import format_float_table

logger = logging.getLogger(__name__)

# --- Constants ------------------------------------------------------------------------------------
# meyere, this needs closed loop and/or variable length returns.
COEFF_COUNT = 2
TARE_COUNT = 1
MASS_SENSOR_COUNT = 1
TEMPERATURE_SENSOR_COUNT = 1

# --- Base Classes ---------------------------------------------------------------------------------
class Command(IntEnum):
    LOOPBACK = 0
    GET_CALIBRATION = 1
    SET_CALIBRATION = 2
    READ_DAC = 3
    READ_UNITS = 4
    SET_PHASE = 5
    POWER_ON_HX711 = 6
    POWER_OFF_HX711 = 7
    TEST = 0xFF

class Response(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4
    MULTI_DATA_POINT = 5
    GET_CALIBRATION = 6
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
        elif packet.header.type == cls.GET_CALIBRATION:
            return RespGetCalibration

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
class Calibration(ctypes.Structure):
    class Field:
        MASS_TEMPERATURE_COEFF = '_mass_temperature_coeff'
        MASS_COEFF = '_mass_coeff'
        TEMPERATURE_COEFF = '_temperature_coeff'
        TARE = '_tare'

    _pack_ = 1
    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * COEFF_COUNT
    _tare_row = ctypes.c_float * TARE_COUNT
    _fields_ = [
        (Field.MASS_TEMPERATURE_COEFF, _row * MASS_SENSOR_COUNT),
        (Field.MASS_COEFF, _row * MASS_SENSOR_COUNT),
        (Field.TEMPERATURE_COEFF, _row * TEMPERATURE_SENSOR_COUNT),
        (Field.TARE, _tare_row * MASS_SENSOR_COUNT)
    ]

    def set_sensor_data(self, field, sensor: int, *values):
        getattr(self, field)[sensor] = values

    @property
    def mass_temperature_coeff(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMPERATURE_COEFF)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @mass_temperature_coeff.setter
    def mass_temperature_coeff(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMPERATURE_COEFF)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def mass_coeff(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.MASS_COEFF)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @mass_coeff.setter
    def mass_coeff(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.MASS_COEFF)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def temperature_coeff(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.TEMPERATURE_COEFF)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @temperature_coeff.setter
    def temperature_coeff(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.TEMPERATURE_COEFF)
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
        coeff_columns = ['Sensor'] + [f'Coefficient {idx}' for idx in range(COEFF_COUNT)]
        tare_columns = ['Sensor'] + [f'Tare {idx}' for idx in range(TARE_COUNT)]

        str_list = [
            format_float_table('Mass/Temperature',
                               coeff_columns, self.mass_temperature_coeff),
            format_float_table('Mass', coeff_columns, self.mass_coeff),
            format_float_table('Temperature', coeff_columns, self.temperature_coeff),
            format_float_table('Tare', tare_columns, self.tare)
        ]

        return '\n\n'.join(str_list)


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
class CmdLoopback(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Command.LOOPBACK


class CmdGetCalibration(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.GET_CALIBRATION
        super().__init__(*args, **kw)

class CmdSetCalibration(BaseCommand):
    class Field(BaseCommand.Field):
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
        kw[self.Field.TYPE] = Command.SET_CALIBRATION
        super().__init__(*args, **kw)



class CmdPowerOnHx711(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.POWER_ON_HX711
        super().__init__(*args, **kw)

class CmdPowerOffHx711(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Command.POWER_OFF_HX711
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

class CmdTest(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Command.TEST


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


class RespGetCalibration(BaseResponse):
    class Field(BaseResponse.Field):
        CALIBRATION = '_calibration'

    _pack_ = 1
    _fields_ = [
        (Field.CALIBRATION, Calibration)
    ]

    @property
    def calibration(self) -> Calibration:
        return getattr(self, self.Field.CALIBRATION)


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