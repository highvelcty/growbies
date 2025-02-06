from enum import IntEnum, StrEnum
from typing import cast, Optional
from typing_extensions import Buffer
import ctypes
import logging
import time

import serial

logger = logging.getLogger(__name__)

class Slip(IntEnum):
    END = 0xC0
    ESC = 0xDB
    ESC_END = 0xDC
    ESC_ESC = 0xDD


class CmdHdr(ctypes.Structure):
    class Cmd(IntEnum):
        LOOPBACK = 0

    _fields_ = [
        ('cmd', ctypes.c_uint16)
    ]

class ArduinoSerial(serial.Serial):
    NUMBER_OF_CHANNELS = 8
    READY_RETRIES = 5
    READY_RETRY_DELAY_SEC = 0.25
    READ_TIMEOUT_SEC = 1
    SLIP_END = b'\xC0'
    class Level1Cmd(StrEnum):
        LOOPBACK = 'loopback'
        SAMPLE = 'sample'

    class Cmd(IntEnum):
        LOOPBACK = 0

    recv_buf = bytearray(64)
    recv_buf_idx = 0
    within_escape = False

    def __init__(self):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        super().__init__(port='/dev/ttyACM0', baudrate=115200, timeout=0.5)

        self._wait_for_ready2()

    def _slip_send_frame(self, buf: bytes):
        for byte in buf:
            if byte == Slip.END:
                self.write(bytes((Slip.ESC, Slip.ESC_END)))
            elif byte == Slip.ESC:
                self.write(bytes((Slip.ESC, Slip.ESC_ESC)))
            else:
                self.write(bytes((byte,)))
        self.write(Slip.END)

    def _slip_decode(self, buf: bytes) -> int:
        num_bytes = self.recv_buf_idx
        for byte in buf:
            if byte == Slip.END:
                self.recv_buf_idx = 0
            elif byte == Slip.ESC:
                self.within_escape = True
            else:
                if self.within_escape:
                    self.within_escape = False
                    if byte == Slip.ESC_END:
                        self.recv_buf[self.recv_buf_idx] = Slip.END
                    elif byte == Slip.ESC_ESC:
                        self.recv_buf[self.recv_buf_idx] = Slip.ESC
                else:
                    self.recv_buf[self.recv_buf_idx] = byte
                self.recv_buf_idx += 1
                num_bytes += 1
        return num_bytes

    def _wait_for_ready(self):
        """From experimentation and quick reading on the internet; it seems that opening a serial
        connection resets the arduino. It takes a few seconds for the arduino serial port to
        stabilize. This method will poll for readiness, blocking until ready or timeout."""
        startt = time.time()
        for retry in range(self.READY_RETRIES):
            if retry:
                time.sleep(self.READY_RETRY_DELAY_SEC)
            bin_data = self.execute(self.Level1Cmd.LOOPBACK, ignore_read_timeout=True)
            if bin_data.decode() == self.Level1Cmd.LOOPBACK:
                logger.info(f'Serial port ready in {time.time() - startt:.02f} seconds.')
                break
        else:
            raise TimeoutError(f'Arduino serial port not ready with {self.READY_RETRIES} retries '
                               f'with {self.READY_RETRY_DELAY_SEC} second delay between tries.')

    def _wait_for_ready2(self):
        startt = time.time()
        for retry in range(self.READY_RETRIES):
            if retry:
                time.sleep(self.READY_RETRY_DELAY_SEC)
            cmd = CmdHdr()
            cmd.cmd = CmdHdr.Cmd.LOOPBACK
            cmd_resp = self.execute2(bytes(cast(Buffer, cmd)), ignore_read_timeout=True)
            if cmd_resp.cmd == CmdHdr.Cmd.LOOPBACK:
                logger.info(f'Serial port ready in {time.time() - startt:.02f} seconds.')
                break
        else:
            raise TimeoutError(f'Arduino serial port not ready with {self.READY_RETRIES} retries '
                               f'with {self.READY_RETRY_DELAY_SEC} second delay between tries.')


    def execute2(self, buf: bytes, *, ignore_read_timeout: bool = False) -> CmdHdr:
        # Send
        self._slip_send_frame(buf)

        # Receive
        if 1: return ''
        startt = time.time()
        while time.time() - startt < self.READ_TIMEOUT_SEC:
            bytes_in_waiting = self.in_waiting
            if bytes_in_waiting:
                buf_len = self._slip_decode(self.read(bytes_in_waiting))

                if buf_len > ctypes.sizeof(CmdHdr):
                    hdr = CmdHdr.from_buffer(cast(Buffer, self.recv_buf))
                    return hdr
        else:
            if not ignore_read_timeout:
                logger.error(f'Arduino serial port read timeout of {self.READ_TIMEOUT_SEC} '
                             f'seconds.')

    def execute(self, cmd: 'Level1Cmd', *, ignore_read_timeout: bool = False) -> bytes:
        out_data = cmd.encode() + self.SLIP_END
        self.write(out_data)
        startt = time.time()
        in_data = bytearray()
        while time.time() - startt < self.READ_TIMEOUT_SEC:
            bytes_in_waiting = self.in_waiting
            if bytes_in_waiting:
                in_data += bytearray(self.read(bytes_in_waiting))
                if in_data[-1] == ord(self.SLIP_END):
                    break
        else:
            if not ignore_read_timeout:
                logger.error(f'Arduino serial port read timeout of {self.READ_TIMEOUT_SEC} '
                             f'seconds.')

        return in_data[:-1]

    def sample(self) -> Optional['Samples']:
        try:
            return Samples.from_buffer(self.execute(self.Level1Cmd.SAMPLE))
        except (ValueError, TypeError):
            logger.exception('Failed to cast sample data to structure.')
        return None

class Samples(ctypes.Structure):
    # noinspection PyTypeChecker
    _fields_ = [
        ('data', ctypes.c_uint16 * ArduinoSerial.NUMBER_OF_CHANNELS)
    ]
