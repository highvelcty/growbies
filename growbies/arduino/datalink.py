from abc import ABC
from enum import IntEnum
import logging

from .base import BaseArduinoSerial

logger = logging.getLogger(__name__)

class Slip(IntEnum):
    END = 0xC0
    ESC = 0xDB
    ESC_END = 0xDC
    ESC_ESC = 0xDD


class ArduinoDatalink(ABC, BaseArduinoSerial):
    READY_RETRIES = 5
    READY_RETRY_DELAY_SEC = 1

    READ_TIMEOUT_SEC = 1

    RECV_BUF_BYTES = 64

    _recv_buf = bytearray(RECV_BUF_BYTES)
    _recv_buf_idx = 0
    _within_escape = False
    _within_frame = False

    def _slip_send_byte(self, byte: int):
        if byte == Slip.END:
            buf = bytes((Slip.ESC, Slip.ESC_END))
            self.write(buf)
        elif byte == Slip.ESC:
            buf = bytes((Slip.ESC, Slip.ESC_ESC))
            self.write(buf)
        else:
            buf = bytes((byte,))
            self.write(buf)

    def _slip_send_end(self):
        self.write(bytes((Slip.END,)))

    def _slip_reset_recv_state(self):
        self._recv_buf_idx = 0
        self._within_escape = False

    def _slip_decode_frame(self, buf: bytes) -> bool:
        for byte in buf:
            if byte == Slip.END:
                return True
            elif byte == Slip.ESC:
                self._within_escape = True
            else:
                if self._within_escape:
                    self._within_escape = False
                    if byte == Slip.ESC_END:
                        self._recv_buf[self._recv_buf_idx] = Slip.END
                    elif byte == Slip.ESC_ESC:
                        self._recv_buf[self._recv_buf_idx] = Slip.ESC
                else:
                    if self._recv_buf_idx < self.RECV_BUF_BYTES:
                        self._recv_buf[self._recv_buf_idx] = byte
                self._recv_buf_idx = min(self._recv_buf_idx + 1, self.RECV_BUF_BYTES)
        return False
