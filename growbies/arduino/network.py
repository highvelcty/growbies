from abc import ABC
from typing import ByteString, Optional
import ctypes
import logging
import time

logger = logging.getLogger(__name__)

from .datalink import ArduinoDatalink
from .structs.command import Packet
from growbies.utils.bufstr import BufStr


class ArduinoNetwork(ArduinoDatalink, ABC):
    CHECKSUM_BYTES = 2
    POLLING_SEC = 0.01
    DEBUG_NETWORK_READ = False
    DEBUG_NETWORK_WRITE = False

    def _send_packet(self, buf: ByteString):
        checksum = ctypes.c_uint16()
        for byte in buf:
            checksum.value += byte
            self._slip_send_byte(byte)
        for byte in memoryview(checksum).cast('B'):
            self._slip_send_byte(byte)
        self._slip_send_end()

        if self.DEBUG_NETWORK_WRITE:
            print(f'Network layer send:\n'
                  f'{BufStr(bytes(buf) + bytes(checksum))}')


    def _recv_packet(self, *,
                     read_timeout_sec:int = ArduinoDatalink.DEFAULT_READ_TIMEOUT_SEC) \
                     -> Optional[Packet]:
        self._slip_reset_recv_state()
        startt = time.time()
        while time.time() - startt < read_timeout_sec:
            bytes_in_waiting = self.in_waiting
            if bytes_in_waiting:
                if self._slip_decode_frame(self.read(bytes_in_waiting)):
                    if self.DEBUG_NETWORK_READ:
                        print(f'Network layer recv:\n'
                              f'{BufStr(self._recv_buf[:self.recv_buf_len()])}')

                    if self.recv_buf_len() > self.CHECKSUM_BYTES:
                        buf = memoryview(self._recv_buf)[:self.recv_buf_len()].cast('B')
                        checksum = ctypes.c_uint16.from_buffer(buf[-self.CHECKSUM_BYTES:]).value
                        calc_checksum = sum(buf[:-self.CHECKSUM_BYTES])
                        if checksum != calc_checksum:
                            logger.error(f'Network layer checksum mismatch.\n'
                                         f'calc: {calc_checksum}, given: {checksum}')
                            return None
                        else:
                            return Packet.make(buf[:-self.CHECKSUM_BYTES])
                    else:
                        logger.error('Network layer packet checksum underflow.')
                        return None
            else:
                time.sleep(self.POLLING_SEC)
        else:
            logger.error(f'Network layer timeout of {read_timeout_sec} seconds waiting for a '
                         f'valid packet.')
            return None
