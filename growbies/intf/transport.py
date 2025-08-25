from abc import ABC
from typing import cast, Optional

from .network import Network
import ctypes
import logging

from .common import Packet
from .cmd import TBaseDeviceCmd
from .resp import DeviceResp, TBaseDeviceResp
from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)


class Transport(Network, ABC):
    DEBUG_TRANSPORT_READ = False
    DEBUG_TRANSPORT_WRITE = False

    def send_cmd(self, cmd: TBaseDeviceCmd):
        if self.DEBUG_TRANSPORT_WRITE:
            print(BufStr(memoryview(cmd).cast('B'), title='Transport Write:'))

        self._send_packet(memoryview(cmd).cast('B'))

    def recv_resp(self, *,
                  read_timeout_sec: float = Network.DEFAULT_READ_TIMEOUT_SEC) \
            -> Optional[TBaseDeviceResp]:
        packet = self._recv_packet(read_timeout_sec=read_timeout_sec)
        if self.DEBUG_TRANSPORT_READ and packet is not None:
            print(BufStr(memoryview(packet).cast('B'), title='Transport Read:'))
        if packet is None:
            return None
        return self._get_resp(packet)

    @staticmethod
    def _get_resp(packet: Packet) -> Optional[TBaseDeviceResp]:
        resp = None
        resp_struct = DeviceResp.get_struct(packet)
        if resp_struct is None:
            logger.error(f'Transport layer unrecognized response type: {packet.header.type}')
        else:
            exp_len = ctypes.sizeof(resp_struct)
            obs_len = ctypes.sizeof(packet)
            if exp_len != obs_len:
                logger.error(f'Transport layer deserializing error to "'
                             f'{resp_struct.__qualname__}", '
                             f'expected {ctypes.sizeof(resp_struct)} bytes, observed {obs_len} bytes.')
            else:
                resp = resp_struct.from_buffer(cast(bytes, packet))

        if not resp:
            buf_str = BufStr(bytes(packet), title='Transport layer received invalid packet.')
            logger.debug(f'\n{buf_str}')

        return resp
