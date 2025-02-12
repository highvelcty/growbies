from abc import ABC
from typing import cast, Optional

from .network import ArduinoNetwork
import ctypes
import logging

from .structs.command import RespType, TBaseCommand, TBaseResponse
from .structs.packet import Packet

logger = logging.getLogger(__name__)


class ArduinoTransport(ArduinoNetwork, ABC):
    def _send_cmd(self, cmd: TBaseCommand):
        self._send_packet(memoryview(cmd).cast('B'))

    def _recv_resp(self) -> Optional[TBaseResponse]:
        packet = self._recv_packet()
        if packet is None:
            logger.error('Packet not received at the transport layer.')
            return
        resp = self._get_resp(packet)
        if resp is None:
            logger.error('Failed to deserialize response from packet.')
        else:
            return resp

    @staticmethod
    def _get_resp(packet: Packet) -> Optional[TBaseResponse]:
        resp_struct = RespType.get_struct(packet.header.type)
        if resp_struct is None:
            logger.error(f'Unrecognized response type: {packet.header.type}')
            return

        exp_len = ctypes.sizeof(resp_struct)
        obs_len = ctypes.sizeof(packet)
        if exp_len != obs_len:
            logger.error(f'Expected {exp_len} bytes for deserializing to "'
                         f'{resp_struct.__qualname__}", observed data payload of {obs_len} bytes.')
            return

        return resp_struct.from_buffer(cast(bytes, packet))
