from typing import ByteString, cast, Optional, TYPE_CHECKING, TypeVar, Union
import ctypes
import logging

if TYPE_CHECKING:
    from ..cmd import DeviceCmd
    from ..resp import DeviceResp
from growbies.utils.bufstr import BufStr
from growbies.utils.report import format_float_list, format_float_table

logger = logging.getLogger(__name__)

__all__ = ['COEFF_COUNT', 'TARE_COUNT', 'MASS_SENSOR_COUNT', 'TEMPERATURE_SENSOR_COUNT',
           'Packet', 'PacketHeader', 'Calibration']

# --- Constants ------------------------------------------------------------------------------------
# meyere, this needs closed loop and/or variable length returns.
COEFF_COUNT = 2
TARE_COUNT = 1
MASS_SENSOR_COUNT = 1
TEMPERATURE_SENSOR_COUNT = 1

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
        TYPE = '_type'
        ID = '_id'

    _pack_ = 1
    _fields_ = [
        (Field.TYPE, ctypes.c_uint16),
        (Field.ID, ctypes.c_uint16),
    ]

    @property
    def id(self) -> int:
        return getattr(self, self.Field.ID)

    @id.setter
    def id(self, value: int):
        setattr(self, self.Field.ID, value)

    @property
    def type(self) -> Union['DeviceCmd', 'DeviceResp']:
        return getattr(self, self.Field.TYPE)

    @type.setter
    def type(self, value: ['DeviceCmd', 'DeviceResp']):
        setattr(self, self.Field.TYPE, value)


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


def _set_ctypes_2d_array(array, values: list[list[float]]):
    for row_idx, row in enumerate(values):
        for column_idx, value in enumerate(row):
            array[row_idx][column_idx] = value

def _get_ctypes_2d_array(array):
    return [list(array[idx]) for idx in range(len(array))]