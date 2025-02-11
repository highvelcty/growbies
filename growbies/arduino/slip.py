from enum import IntEnum
from typing import ByteString, cast, Optional
import logging
import time

import serial

from . import structs

logger = logging.getLogger(__name__)

class Slip(IntEnum):
    END = 0xC0
    ESC = 0xDB
    ESC_END = 0xDC
    ESC_ESC = 0xDD


class ArduinoSerial(serial.Serial):
    DEBUG_SEND = True
    DEBUG_RECV = True

    READY_RETRIES = 5
    READY_RETRY_DELAY_SEC = 1

    EXEC_RETRIES = 3
    EXEC_RETRY_DELAY_SEC = 0.25

    READ_TIMEOUT_SEC = 1

    RECV_BUF_BYTES = 64

    _recv_buf = bytearray(RECV_BUF_BYTES)
    _recv_buf_idx = 0
    _within_escape = False
    _within_frame = False

    def __init__(self):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        super().__init__(port='/dev/ttyACM0', baudrate=115200, timeout=0.5)

        self._wait_for_ready()

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

    def _slip_send_packet(self, packet: structs.Packet):
        for byte in memoryview(cast(bytes, packet)).cast('B'):
            self._slip_send_byte(byte)
        buf = bytes((Slip.END,))
        self.write(buf)

    def _reset_slip_recv_state(self):
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

    def _wait_for_ready(self) -> structs.RespLoopback:
        cmd = structs.CommandLoopback()
        for ii in range(len(cmd.payload)):
            cmd.payload[ii] = ii
        resp: Optional[structs.RespLoopback] = (
            self.execute(cmd,
                         retries=self.READY_RETRIES,
                         retry_delay_sec=self.READY_RETRY_DELAY_SEC))
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
        if not resp.is_valid():
            logger.error(f'Command "{cmd.__qualname__}" payload contents.\n'
                         f'  exp: {bytes(resp.payload)}\n'
                         f'  obs: {bytes(cmd.payload)}')
        return resp

    def execute(self, cmd: structs.TBaseCommand, *,
                retries: int = EXEC_RETRIES,
                retry_delay_sec: float = EXEC_RETRY_DELAY_SEC) -> Optional[structs.TBaseResponse]:
        for retry in range(retries):
            if retry:
                time.sleep(retry_delay_sec)

            # Send
            self._slip_send_packet(structs.Packet.from_command(cmd))

            # Receive
            self._reset_slip_recv_state()
            startt = time.time()
            while time.time() - startt < self.READ_TIMEOUT_SEC:
                bytes_in_waiting = self.in_waiting
                if bytes_in_waiting:
                    if self._slip_decode_frame(self.read(bytes_in_waiting)):
                        packet = structs.Packet.make(
                            memoryview(self._recv_buf)[:self._recv_buf_idx])
                        if not packet:
                            logger.error('Failed to decode SLIP frame to packet.')
                            break
                        else:
                            payload = packet.get_payload()
                            if payload is None:
                                logger.error('Failed to deserialize response from packet.')
                                break
                            else:
                                return payload
            else:
                logger.error(f'Timeout of {self.READ_TIMEOUT_SEC} seconds waiting for command '
                             f'response.')
        else:
            logger.error(f'Exhausted {self.EXEC_RETRIES} retries executing command '
                         f'{bytes(cmd)}.')

    def sample(self) -> int:
        cmd = structs.CommandSample()
        resp: structs.RespSample = self.execute(cmd)
        return resp.sample

    def read(self, size=1) -> bytes:
        buf = super().read(size)
        if self.DEBUG_RECV: print(f'python recv: {buf}')
        return buf

    def write(self, buf: ByteString):
        if self.DEBUG_SEND: print(f'python send: {buf}')
        super().write(buf)

