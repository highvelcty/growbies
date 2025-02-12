from typing import ByteString, cast, Optional, Sequence, Union
import ctypes
import logging

from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)


class PacketHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('type', ctypes.c_uint16),
    ]

    @property
    def type(self) -> ctypes.c_uint16:
        return super().type

    @type.setter
    def type(self, value: ctypes.c_uint16):
        super().type = value

    def __str__(self):
        return BufStr(memoryview(self).cast('B'))


class Packet(object):
    MIN_SIZE_IN_BYTES = ctypes.sizeof(PacketHeader)

    @classmethod
    def make(cls, source: Union[ByteString, int]) -> Optional['Packet']:
        if isinstance(source, int):
            source = bytearray(source)
        buf_len = len(source)
        data_len = buf_len - cls.MIN_SIZE_IN_BYTES
        class NewPacket(Packet, ctypes.Structure):
            _fields_ = [
                ('header', PacketHeader),
                ('data', ctypes.c_uint8 * data_len) # noqa - false positive pycharm 2025
            ]
            _pack_ = 1

        if buf_len < Packet.MIN_SIZE_IN_BYTES:
            logger.error(f'Buffer underflow for deserializing to {Packet.__class__}. '
                         f'Expected at least {Packet.MIN_SIZE_IN_BYTES} bytes, '
                         f'observed {buf_len} bytes.')
            return

        packet = NewPacket.from_buffer(cast(bytes, source))

        return packet

    @property
    def header(self) -> PacketHeader:
        return getattr(self, 'header')

    @property
    def data(self) -> ctypes.Array[ctypes.c_uint8]:
        return getattr(self, 'data')