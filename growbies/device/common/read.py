import ctypes
from ctypes import sizeof
from enum import IntEnum
from typing import Any

from growbies.service.common import ServiceCmdError
from .common import BaseStructure

class EndpointType(IntEnum):
    MASS = 0,
    TEMPERATURE = 1
    TARE_CRC = 2


class TLVHdr(BaseStructure):
    class Field(BaseStructure.Field):
        TYPE = '_type'
        LENGTH = '_length'

    _fields_ = [
        (Field.TYPE, ctypes.c_uint8),
        (Field.LENGTH, ctypes.c_uint8)
    ]

    @property
    def type(self) -> EndpointType:
        return EndpointType(getattr(self, self.Field.TYPE))

    @type.setter
    def type(self, value: EndpointType):
        setattr(self, self.Field.TYPE, value)

    @property
    def length(self) -> int:
        return getattr(self, self.Field.LENGTH)

    @length.setter
    def length(self, value: int):
        setattr(self, self.Field.LENGTH, value)

class DataPoint:
    def __init__(self, buf: bytearray):
        self._type_vals = dict()

        offset = 0
        while offset <= len(buf) - sizeof(TLVHdr):
            hdr = TLVHdr.from_buffer(buf, offset)
            offset += sizeof(hdr)

            self._type_vals[hdr.type] = list()
            if hdr.type in (EndpointType.MASS, EndpointType.TARE_CRC):
                klass = ctypes.c_float
            else:
                raise ServiceCmdError('Unknown ')

            required = hdr.length * sizeof(klass)
            if offset + required > len(buf):
                raise ServiceCmdError(f'Buffer underflow while deserializing to'
                                      f'{DataPoint.__qualname__}')
            else:
                for ii in range(hdr.length // sizeof(klass)):
                    self._type_vals[hdr.type].append(klass.from_buffer(buf, offset))
                    offset += sizeof(klass)

    def __str__(self) -> str:
        lines = [f'{DataPoint.__qualname__}:']
        for ep_type, vals in self._type_vals.items():
            if not vals:
                continue

            # Format label and units
            label = ep_type.name.capitalize()
            if ep_type == EndpointType.MASS:
                formatted_vals = ", ".join(f"{v:.2f}" for v in vals[:-1])
                total = vals[-1]
                lines.append(f"{label}: {formatted_vals} | Total: {total:.2f}")
            elif ep_type == EndpointType.TEMPERATURE:
                formatted_vals = ", ".join(f"{v:.2f}" for v in vals[:-1])
                avg = vals[-1]
                lines.append(f"{label}: {formatted_vals} | Avg: {avg:.2f}")
            elif ep_type == EndpointType.TARE_CRC:
                lines.append(f"{label}: 0x{vals[0]:.0f}")
            else:
                lines.append(f"{label}: {', '.join(str(v) for v in vals)}")

        return "\n".join(lines)

    def endpoint_values(self) -> dict[EndpointType, Any]:
        return self._type_vals
