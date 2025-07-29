from enum import IntEnum
from typing import ByteString, cast, Optional, NewType, Type, TypeVar, Union
import ctypes
import logging

from growbies.utils.bufstr import BufStr
from growbies.utils.report import format_float_list, format_float_table

logger = logging.getLogger(__name__)

# --- Constants ------------------------------------------------------------------------------------
# meyere, this needs closed loop and/or variable length returns.
COEFF_COUNT = 2
TARE_COUNT = 1
MASS_SENSOR_COUNT = 3
TEMPERATURE_SENSOR_COUNT = 3

# --- Base Classes ---------------------------------------------------------------------------------
class Cmd(IntEnum):
    LOOPBACK = 0
    GET_CALIBRATION = 1
    SET_CALIBRATION = 2
    READ_UNITS = 3
    POWER_ON_HX711 = 4
    POWER_OFF_HX711 = 5

class Resp(IntEnum):
    VOID = 0
    BYTE = 1
    LONG = 2
    FLOAT = 3
    DOUBLE = 4
    READ_UNITS = 5
    GET_CALIBRATION = 6
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
        elif packet.header.type == cls.READ_UNITS:
            return RespMultiDataPoint
        elif packet.header.type == cls.GET_CALIBRATION:
            return RespGetCalibration

        logger.error(f'Transport layer unrecognized response type: {packet.header.type}')
        return None


error_t = ctypes.c_uint32
class Error(IntEnum):
    # bitfield
    NONE                                  = 0x00000000
    CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 0x00000001
    UNRECOGNIZED_COMMAND                  = 0x00000002
    OUT_OF_THRESHOLD_SAMPLE               = 0x00000004
    HX711_NOT_READY                       = 0x00000008

class Phase(IntEnum):
    A = 0
    B = 1

unit_t = ctypes.c_uint16
class Unit(IntEnum):
    # Bitfield
    UNIT_GRAMS          = 0x0001
    UNIT_MASS_DAC       = 0x0002
    UNIT_TEMP_DAC       = 0x0004
    UNIT_CELSIUS        = 0x0008

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
    def type(self) -> Union[Cmd, Resp]:
        return super().type.value

    @type.setter
    def type(self, value: [Cmd, Resp]):
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
    class Field(PacketHeader.Field):
        ERROR = '_error'

    _pack_ = 1
    _fields_ = [
        (Field.ERROR, error_t)
    ]

    @property
    def error(self) -> Error:
        return getattr(self, self.Field.ERROR)

    @error.setter
    def error(self, error: Error):
        setattr(self, self.Field.ERROR, error)

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
        TARE = '_tare'

    _pack_ = 1
    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * COEFF_COUNT
    _fields_ = [
        (Field.MASS_TEMPERATURE_COEFF, _row * MASS_SENSOR_COUNT),
        (Field.MASS_COEFF, ctypes.c_float * COEFF_COUNT),
        (Field.TARE, ctypes.c_float * TARE_COUNT)
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
    def mass_coeff(self) -> list[float]:
        return list(getattr(self, self.Field.MASS_COEFF))

    @mass_coeff.setter
    def mass_coeff(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.MASS_COEFF))):
            getattr(self, self.Field.MASS_COEFF)[idx] = values[idx]

    @property
    def tare(self) -> list[float]:
        return list(getattr(self, self.Field.TARE))

    @tare.setter
    def tare(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.TARE))):
            getattr(self, self.Field.TARE)[idx] = values[idx]

    def __str__(self):
        coeff_columns = [f'Coeff {idx}' for idx in range(COEFF_COUNT)]
        sensor_coeff_columns = ['Sensor'] + coeff_columns
        tare_columns = [f'Slot {idx}' for idx in range(TARE_COUNT)]

        str_list = [
            format_float_table('Mass/Temperature Compensation',
                               sensor_coeff_columns,
                               self.mass_temperature_coeff),
            format_float_list('Mass Calibration Coefficients', coeff_columns, self.mass_coeff),
            format_float_list('Tare', tare_columns, self.tare)
        ]

        return '\n\n'.join(str_list)


# --- Commands -------------------------------------------------------------------------------------
class CmdLoopback(BaseCommand):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.type = Cmd.LOOPBACK


class CmdGetCalibration(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.GET_CALIBRATION
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
        kw[self.Field.TYPE] = Cmd.SET_CALIBRATION
        super().__init__(*args, **kw)

class CmdPowerOnHx711(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.POWER_ON_HX711
        super().__init__(*args, **kw)

class CmdPowerOffHx711(BaseCommand):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.POWER_OFF_HX711
        super().__init__(*args, **kw)

class CmdReadUnits(BaseCmdWithTimesParam):
    class Field(BaseCmdWithTimesParam.Field):
        UNITS = '_units'

    _fields_ = [
        (Field.UNITS, unit_t)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Cmd.READ_UNITS
        super().__init__(*args, **kw)

    @property
    def units(self) -> unit_t:
        return getattr(self, self.Field.UNITS)

    @units.setter
    def units(self, val: unit_t):
        setattr(self, self.Field.UNITS, val)

# --- Responses ------------------------------------------------------------------------------------
class RespVoid(BaseResponse):
    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.VOID
        super().__init__(*args, **kw)


class BaseRespWithData(BaseResponse):
    class Field(BaseResponse.Field):
        DATA = 'data'


class RespByte(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_uint8)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.BYTE
        super().__init__(*args, **kw)


class RespLong(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_int32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.LONG
        super().__init__(*args, **kw)


class RespFloat(BaseRespWithData):
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.FLOAT
        super().__init__(*args, **kw)


class RespDouble(BaseRespWithData):
    """Arduino uno has 4 byte double, the same as a float."""
    _fields_ = [
        (BaseRespWithData.Field.DATA, ctypes.c_float)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.DOUBLE
        super().__init__(*args, **kw)


class RespError(BaseResponse):
    class Field(BaseResponse.Field):
        ERROR = 'error'

    _fields_ = [
        (Field.ERROR, ctypes.c_uint32)
    ]

    def __init__(self, *args, **kw):
        kw[self.Field.TYPE] = Resp.ERROR
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
        MASS_SENSOR = '_mass_sensor'
        MASS = '_mass'
        TEMPERATURE_SENSOR = '_temperature_sensor'
        TEMPERATURE = '_temperature'

    _pack_ = 1
    _fields_ = [
        (Field.MASS_SENSOR, ctypes.c_float * MASS_SENSOR_COUNT),
        (Field.MASS, ctypes.c_float),
        (Field.TEMPERATURE_SENSOR, ctypes.c_float * TEMPERATURE_SENSOR_COUNT),
        (Field.TEMPERATURE, ctypes.c_float)
    ]

    @property
    def mass_sensor(self) -> list[float]:
        return list(getattr(self, self.Field.MASS_SENSOR))

    @property
    def mass(self) -> float:
        return getattr(self, self.Field.MASS)

    @property
    def temperature_sensor(self) -> list[float]:
        return list(getattr(self, self.Field.TEMPERATURE_SENSOR))

    @property
    def temperature(self) -> float:
        return getattr(self, self.Field.TEMPERATURE)

    def __str__(self):
        str_list = list()
        for idx, val in enumerate(self.mass_sensor):
            str_list.append(f'mass_sensor_{idx}: {val}')
        str_list.append(f'mass: {self.mass}')
        str_list.append('')
        for idx, val in enumerate(self.temperature_sensor):
            str_list.append(f'temperature_sensor_{idx}: {val}')
        str_list.append(f'temperature: {self.temperature}')
        return '\n'.join(str_list)

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