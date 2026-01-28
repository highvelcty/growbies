import ctypes
from .common import  BaseStructure

class DeviceLog(BaseStructure):
    VERSION = 1
    MAX_MSG = 128

    class Field(BaseStructure.Field):
        LEVEL = '_level'
        MSG = '_msg'

    _fields_ = [
        (Field.LEVEL, ctypes.c_uint8),
        (Field.MSG, ctypes.c_char * MAX_MSG)
    ]

    @property
    def level(self) -> int:
        return getattr(self, self.Field.LEVEL)

    @property
    def msg(self) -> str:
        raw = getattr(self, self.Field.MSG)
        return bytes(raw[:]).decode('utf-8', errors='replace')
