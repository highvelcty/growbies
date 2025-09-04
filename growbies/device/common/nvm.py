import ctypes

from .common import BaseStructure

class NvmHeader(BaseStructure):
    class Field(BaseStructure.Field):
        MAGIC = '_magic'
        VERSION = '_version'

    _pack_ = 1
    _fields_ = [
        (Field.MAGIC, ctypes.c_uint16),
        (Field.VERSION, ctypes.c_uint16)
    ]

    @property
    def magic(self) -> int:
        return getattr(self, self.Field.MAGIC)

    @property
    def version(self) -> int:
        return getattr(self, self.Field.VERSION)
