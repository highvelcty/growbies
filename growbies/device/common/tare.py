import ctypes

from . import nvm
from .common import BaseStructure
from growbies.utils.report import format_float_list

class Tare(BaseStructure):
    TARE_COUNT = 8

    class Field(BaseStructure.Field):
        VALUES = '_values'

    _fields_ = [
        (Field.VALUES, ctypes.c_float * TARE_COUNT),
    ]

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
        ]

        return '\n\n'.join(str_list)

class NvmTare(nvm.BaseNvm):
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Tare)
    ]

    @property
    def payload(self) -> Tare:
        return super().payload

    @payload.setter
    def payload(self, value: Tare):
        super().payload = value
