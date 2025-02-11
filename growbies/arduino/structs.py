from enum import IntEnum
from typing import ByteString, cast, Optional, TypeVar, Union
import ctypes
import logging

logger = logging.getLogger(__name__)

class PacketHeader(ctypes.Structure):
    _fields_ = [
        ('command', ctypes.c_uint16),
    ]

class BaseStruct(ctypes.Structure):
    _pack_ = 1
TBaseStruct = TypeVar('TBaseStruct', bound=BaseStruct)

class BaseCommand(BaseStruct):
    pass
TBaseCommand = TypeVar('TBaseCommand', bound=BaseCommand)


class BaseResponse(ctypes.Structure):
    pass
TBaseResponse = TypeVar('TBaseResponse', bound=BaseResponse)


class Packet(object):
    CHECKSUM_BYTES = 2
    MIN_SIZE_IN_BYTES = ctypes.sizeof(PacketHeader) + CHECKSUM_BYTES
    _DATA_FIELD_IDX = 2

    class Command(IntEnum):
        LOOPBACK = 0
        SAMPLE = 1

    @classmethod
    def make(cls, source: Union[ByteString, int]) -> Optional['Packet']:
        validate_checksum = True
        if isinstance(source, int):
            source = bytearray(source)
        data_len = len(source) - cls.MIN_SIZE_IN_BYTES
        class NewPacket(Packet, ctypes.Structure):
            _fields_ = [
                ('header', PacketHeader),
                ('data', ctypes.c_uint8 * data_len), # noqa
                ('checksum', ctypes.c_uint16)
            ]
            _pack_ = 1

        buf_len = len(source)

        if buf_len < Packet.MIN_SIZE_IN_BYTES:
            logger.error(f'Buffer underflow for deserializing to {Packet.__class__}. '
                         f'Expected at least {Packet.MIN_SIZE_IN_BYTES} bytes, '
                         f'observed {buf_len} bytes.')
            return

        packet = NewPacket.from_buffer(cast(bytes, source))

        if validate_checksum and not packet.validate_checksum():
            logger.error('Packet checksum mismatch.')
            return
        return packet

    @classmethod
    def from_command(cls, cmd_struct: TBaseCommand):
        if isinstance(cmd_struct, CommandLoopback):
            command = Packet.Command.LOOPBACK
        elif isinstance(cmd_struct, CommandSample):
            command = Packet.Command.SAMPLE
        else:
            raise Exception(f'No command value mapping for structure "{cmd_struct.__class__}"')

        packet = cls.make(cls.MIN_SIZE_IN_BYTES + ctypes.sizeof(cmd_struct))
        packet.header.command = command
        ctypes.memmove(ctypes.addressof(packet.data), ctypes.addressof(cmd_struct),
                       ctypes.sizeof(cmd_struct))
        packet.update_checksum()
        return packet

    def get_payload(self) -> Optional[TBaseResponse]:
        if self.header.command == Packet.Command.LOOPBACK:
            resp_struct = RespLoopback
        elif self.header.command == Packet.Command.SAMPLE:
            resp_struct = RespSample
        else:
            logger.error(f'Unrecognized command {self.header.command}')
            return

        exp_len = ctypes.sizeof(resp_struct)
        obs_len = ctypes.sizeof(self.data)
        if exp_len != obs_len:
            logger.error(f'Expected {exp_len} bytes for deserializing to "'
                         f'{resp_struct.__qualname__}", observed data payload of {obs_len} bytes.')
            return

        return resp_struct.from_buffer(cast(bytes,self.data))

    @property
    def checksum(self) -> int:
        return getattr(self, 'checksum')

    @property
    def data(self) -> ctypes.Array[ctypes.c_uint8]:
        return getattr(self, 'data')

    @property
    def header(self) -> PacketHeader:
        return getattr(self, 'header')

    def calc_checksum(self) -> int:
        return sum(memoryview(cast(bytes, self)).cast('B')[:-self.CHECKSUM_BYTES])

    def update_checksum(self) -> int:
        checksum = self.calc_checksum()
        setattr(self, 'checksum', checksum)
        return checksum

    def validate_checksum(self) -> bool:
        return self.calc_checksum() == self.checksum

class CommandLoopback(BaseCommand):
    fields = [
        ('payload', ctypes.c_uint8 * 4) # noqa
    ]
    _fields_ = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for ii in range(ctypes.sizeof(self)):
            self.payload[ii] = ii

    @property
    def payload(self):
        return super().payload


class RespLoopback(BaseResponse):
    _fields_ = CommandLoopback.fields

    def is_valid(self):
        for ii in range(ctypes.sizeof(self)):
            if self.payload[ii] != ii:
                return False
        return True

class CommandSample(BaseCommand):
    pass

class RespSample(BaseResponse):
    _fields_ = [
        ('sample', ctypes.c_int32)
    ]

    @property
    def sample(self) -> int:
        return super().sample
