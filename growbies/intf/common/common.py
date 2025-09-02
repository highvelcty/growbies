from typing import ByteString, cast, Optional, TYPE_CHECKING, TypeVar, Union
import ctypes
import logging

if TYPE_CHECKING:
    from ..cmd import DeviceCmd
    from ..resp import DeviceResp

from growbies.utils.bufstr import BufStr
from growbies.service.resp.structs import ServiceCmdError

logger = logging.getLogger(__name__)

__all__ = ['BaseStructure', 'Packet', 'PacketHeader']

# --- Constants ------------------------------------------------------------------------------------

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
                (cls.Field.HEADER, PacketHeader),
                (cls.Field.DATA, ctypes.c_uint8 * data_len) # noqa - false positive pycharm 2025
            ]


        if buf_len < Packet.MIN_SIZE_IN_BYTES:
            raise ServiceCmdError(f'Buffer underflow for deserializing to {Packet.__class__}. '
                         f'Expected at least {Packet.MIN_SIZE_IN_BYTES} bytes, '
                         f'observed {buf_len} bytes.')

        packet = _Packet.from_buffer_copy(cast(bytes, source))

        return packet

    @property
    def header(self) -> PacketHeader:
        return getattr(self, self.Field.HEADER)

    @property
    def data(self) -> ctypes.Array[ctypes.c_uint8]:
        return getattr(self, self.Field.DATA)
