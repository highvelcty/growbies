from enum import Enum
from typing import Any, ByteString, cast, Iterator, TYPE_CHECKING, TypeVar, Union, NewType
import ctypes
import logging

if TYPE_CHECKING:
    from ..cmd import DeviceCmd
    from ..resp import DeviceResp

from growbies.utils.bufstr import BufStr
from growbies.service.resp.structs import ServiceCmdError

logger = logging.getLogger(__name__)

__all__ = ['BaseStructure', 'TBaseStructure', 'Packet', 'PacketHdr']

# --- Constants ------------------------------------------------------------------------------------

class BaseStructure(ctypes.Structure):
    @classmethod
    def qualname(cls):
        return cls.__qualname__

    def buf_str(self):
        return str(BufStr(memoryview(self).cast('B'),
                          title=self.qualname()))

    @classmethod
    def all_fields(cls) -> list[tuple[str, type[Any], int, int]]:
        """
        Returns a list of all fields in memory layout, including inherited fields.
        Derived class fields override base class fields with the same name.
        Each item is a tuple: (field_name, field_type, offset, size)
        """
        seen = {}
        # Walk MRO from base -> derived
        for base in cls.__mro__[::-1]:
            if (issubclass(base, ctypes.Structure) and
                    hasattr(base, '_fields_') and base is not ctypes.Structure):
                for field_name, field_type in base._fields_:
                    # override previous base field if derived redefines it
                    seen[field_name] = (field_name, field_type,
                                        getattr(cls, field_name).offset, ctypes.sizeof(field_type))
        # preserve order in memory layout
        return list(seen.values())

    @classmethod
    def describe_layout(cls):
        print(f"{cls.__qualname__} sizeof = {ctypes.sizeof(cls)}")
        for name, ftype, offset, size in cls.all_fields():
            print(f"  {name:<24} offset={offset:3} size={size:3} type={ftype}")

    def get_str(self, prefix: str = ''):
        str_list = list()
        for field_name, field_type, field_offset, field_size in self.all_fields():
            stripped_name = field_name.lstrip('_')
            if field_name in getattr(self, '_anonymous_', []):
                next_name = f'{prefix}'
            else:
                next_name = f'{prefix}.{stripped_name}' if prefix else stripped_name
            if issubclass(field_type, ctypes.Structure):
                str_list.append(
                    getattr(self, stripped_name).get_str(next_name))
            else:
                # full_name = f'{prefix}{stripped_name}' if prefix else stripped_name
                str_list.append(f'0x{field_offset:04X} '
                                f'{next_name}:' 
                                f' {repr(getattr(self, stripped_name))}')
        return '\n'.join(str_list)

    def __str__(self):
        return self.get_str()
TBaseStructure = NewType('TBaseStructure', BaseStructure)

class PacketHdr(BaseStructure):
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


class Packet(BaseStructure):
    MIN_SIZE_IN_BYTES = ctypes.sizeof(PacketHdr)

    class Field:
        HDR = '_header'
        DATA = '_data'

    @classmethod
    def make(cls, source: Union[ByteString, int]) -> 'Packet':
        """
        raises:
            :class:`ServiceCmdError`
        """
        if isinstance(source, int):
            source = bytearray(source)
        buf_len = len(source)
        data_len = buf_len - cls.MIN_SIZE_IN_BYTES
        class _Packet(Packet):
            _pack_ = 1
            _fields_ = [
                (cls.Field.HDR, PacketHdr),
                (cls.Field.DATA, ctypes.c_uint8 * data_len) # noqa - false positive pycharm 2025
            ]


        if buf_len < Packet.MIN_SIZE_IN_BYTES:
            raise ServiceCmdError(f'Buffer underflow for deserializing to {Packet.__class__}. '
                         f'Expected at least {Packet.MIN_SIZE_IN_BYTES} bytes, '
                         f'observed {buf_len} bytes.')

        packet = _Packet.from_buffer_copy(cast(bytes, source))

        return packet

    @property
    def hdr(self) -> PacketHdr:
        return getattr(self, self.Field.HDR)

    @property
    def data(self) -> ctypes.Array[ctypes.c_uint8]:
        return getattr(self, self.Field.DATA)
