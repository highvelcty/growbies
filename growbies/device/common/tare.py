import ctypes

from .common import BaseStructure
from growbies.utils.report import format_float_list

class Tare(BaseStructure):
    TARE_COUNT = 8

    class Field(BaseStructure.Field):
        VALUES = '_values'
        CRC = '_crc'

    _fields_ = [
        (Field.VALUES, ctypes.c_float * TARE_COUNT),
        (Field.CRC, ctypes.c_uint16),
    ]

    @property
    def crc(self) -> int:
        return getattr(self, self.Field.CRC)

    @crc.setter
    def crc(self, value: int):
        setattr(self, self.Field.CRC, value)

    @property
    def values(self) -> list[float]:
        return list(getattr(self, self.Field.VALUES))

    @values.setter
    def values(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.VALUES))):
            getattr(self, self.Field.VALUES)[idx] = values[idx]

    def __str__(self):
        tare_columns = [f'Tare {idx}' for idx in range(self.TARE_COUNT)]

        str_list = [
            format_float_list('Tare Values', tare_columns, self.values),
            f'CRC: 0x{self.crc:04X}'
        ]

        return '\n\n'.join(str_list)
