import ctypes

from .common import BaseStructure

class NvmHdr(BaseStructure):
    class Field(BaseStructure.Field):
        VERSION = '_version'
        RESERVED0 = '_reserved0'
        CRC = '_crc'
        LENGTH = '_length'
        RESERVED1 = '_reserved1'

    _fields_ = [
        (Field.VERSION, ctypes.c_uint8),
        (Field.RESERVED0, ctypes.c_uint8),
        (Field.CRC, ctypes.c_uint16),
        (Field.LENGTH, ctypes.c_uint16),
        (Field.RESERVED1, ctypes.c_uint16)
    ]

    @property
    def crc(self) -> int:
        return getattr(self, self.Field.CRC)

    @crc.setter
    def crc(self, value: int):
        setattr(self, self.Field.CRC, value)

    @property
    def length(self) -> int:
        return getattr(self, self.Field.LENGTH)

    @length.setter
    def length(self, value: int):
        setattr(self, self.Field.LENGTH, value)

    @property
    def reserved0(self) -> int:
        return getattr(self, self.Field.RESERVED0)

    @property
    def reserved1(self) -> int:
        return getattr(self, self.Field.RESERVED1)

    @property
    def version(self) -> int:
        return getattr(self, self.Field.VERSION)

    @version.setter
    def version(self, value: int):
        setattr(self, self.Field.VERSION, value)

class BaseNvm(BaseStructure):
    class Field(BaseStructure.Field):
        HDR = '_hdr'
        PAYLOAD = '_payload'

    @property
    def hdr(self) -> NvmHdr:
        return getattr(self, self.Field.HDR)

    @hdr.setter
    def hdr(self, value: NvmHdr):
        setattr(self, self.Field.HDR, value)

    @property
    def payload(self):
        return getattr(self, self.Field.PAYLOAD)

    @payload.setter
    def payload(self, value):
        setattr(self, self.Field.PAYLOAD, value)
