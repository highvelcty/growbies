from abc import ABC
from typing import ByteString, cast, Optional, Union
import ctypes
import logging
import time

logger = logging.getLogger(__name__)

from .datalink import ArduinoDatalink
from .structs.packet import Packet


class ArduinoNetwork(ArduinoDatalink, ABC):
    CHECKSUM_BYTES = 2

    def _send_packet(self, buf: ByteString):
        checksum = ctypes.c_uint16()
        for byte in buf:
            checksum.value += byte
            self._slip_send_byte(byte)
        for byte in memoryview(checksum).cast('B'):
            self._slip_send_byte(byte)
        self._slip_send_end()

    def _recv_packet(self) -> Packet:
        self._slip_reset_recv_state()
        startt = time.time()
        while time.time() - startt < self.READ_TIMEOUT_SEC:
            bytes_in_waiting = self.in_waiting
            if bytes_in_waiting:
                if self._slip_decode_frame(self.read(bytes_in_waiting)):
                    buf = memoryview(self._recv_buf)[:self._recv_buf_idx].cast('B')
                    checksum = ctypes.c_uint16.from_buffer(buf[-self.CHECKSUM_BYTES:]).value
                    calc_checksum = sum(buf[:-self.CHECKSUM_BYTES])
                    if checksum != calc_checksum:
                        logger.error(f'Checksum mismatch. calc: {calc_checksum}, given: {checksum}')
                        break
                    else:
                        return Packet.make(buf[:-self.CHECKSUM_BYTES])
        else:
            logger.error(f'Timeout of {self.READ_TIMEOUT_SEC} seconds waiting for a valid packet.')
