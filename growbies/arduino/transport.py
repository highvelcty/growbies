from abc import ABC
from typing import cast, Optional

from .network import ArduinoNetwork
import ctypes
import logging

from .structs.command import Packet, RespType, TBaseCommand, TBaseResponse
from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)


class ArduinoTransport(ArduinoNetwork, ABC):
    DEBUG_TRANSPORT_READ = True
    DEBUG_TRANSPORT_WRITE = False

    def _send_cmd(self, cmd: TBaseCommand):
        if self.DEBUG_TRANSPORT_WRITE:
            print(BufStr(memoryview(cmd).cast('B'), title='Transport Write:'))

        self._send_packet(memoryview(cmd).cast('B'))

    def _recv_resp(self, *,
                   read_timeout_sec = ArduinoNetwork.DEFAULT_READ_TIMEOUT_SEC) \
            -> Optional[TBaseResponse]:
        packet = self._recv_packet(read_timeout_sec=read_timeout_sec)
        if self.DEBUG_TRANSPORT_READ and packet is not None:
            print(BufStr(memoryview(packet).cast('B'), title='Transport Read:'))
        if packet is None:
            return None
        return self._get_resp(packet)

    @staticmethod
    def _get_resp(packet: Packet) -> Optional[TBaseResponse]:
        resp_struct = RespType.get_struct(packet)
        if resp_struct is None:
            logger.error(f'Transport layer unrecognized response type: {packet.header.type}')
            return None

        exp_len = ctypes.sizeof(resp_struct)
        obs_len = ctypes.sizeof(packet)
        if exp_len != obs_len:
            logger.error(f'Transport layer expected {exp_len} bytes for deserializing to "'
                         f'{resp_struct.__qualname__}", observed data payload of {obs_len} bytes.')
            return None

        return resp_struct.from_buffer(cast(bytes, packet))
