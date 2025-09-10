import ctypes

from .common import BaseStructure

class NvmHeader(BaseStructure):
    class Field(BaseStructure.Field):
        MAGIC = '_magic'

    _pack_ = 1
    _fields_ = [
        (Field.MAGIC, ctypes.c_uint16),
    ]

    @property
    def magic(self) -> int:
        return getattr(self, self.Field.MAGIC)

    @magic.setter
    def magic(self, value: int):
        setattr(self, self.Field.MAGIC, value)
