from enum import IntEnum
from typing import cast, Optional
from typing_extensions import Buffer
import ctypes
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
    READY_RETRIES = 5
    READY_RETRY_DELAY_SEC = 0.25
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
            self.write(bytes((Slip.ESC, Slip.ESC_END)))
        elif byte == Slip.ESC:
            self.write(bytes((Slip.ESC, Slip.ESC_ESC)))
        else:
            self.write(bytes((byte,)))

    def _slip_send_packet(self, packet: structs.Packet):
        for byte in memoryview(cast(Buffer, packet)).cast('B'):
            self._slip_send_byte(byte)
        self.write(bytes((Slip.END,)))

    def _reset_slip_recv_state(self):
        self._recv_buf_idx = 0
        self._within_escape = False

    def _slip_decode_frame(self, buf: bytes) -> Optional[bytearray]:
        for byte in buf:
            if byte == Slip.END:
                return self._recv_buf[:self._recv_buf_idx]
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

    def _wait_for_ready(self):
        startt = time.time()
        for retry in range(self.READY_RETRIES):
            if retry:
                time.sleep(self.READY_RETRY_DELAY_SEC)
            packet = structs.Packet.from_command(structs.CommandLoopback())
            cmd_resp = self.execute(bytes(cast(Buffer, cmd)), ignore_read_timeout=False)
            if cmd_resp.cmd == structs.Packet.Command.LOOPBACK:
                logger.info(f'Serial port ready in {time.time() - startt:.02f} seconds.')
                break
        else:
            raise TimeoutError(f'Arduino serial port not ready with {self.READY_RETRIES} retries '
                               f'with {self.READY_RETRY_DELAY_SEC} second delay between tries.')

    def exec(self, command: structs.BaseCommand) -> structs.BaseResponse:
        self._slip_send_packet(structs.Packet.from_command(command))


    def execute(self, buf: bytes, *, ignore_read_timeout: bool = False) -> structs.Packet:
        # Send
        self._slip_send_packet(buf)
        return ''

        print(f'emey start recv')
        # Receive       
        startt = time.time()
        while time.time() - startt < self.READ_TIMEOUT_SEC:
            bytes_in_waiting = self.in_waiting            
            if bytes_in_waiting:
                buf_len = self._slip_decode_frame(self.read(bytes_in_waiting))

                if buf_len > ctypes.sizeof(CommandHeader):
                    hdr = CommandHeader.from_buffer(cast(Buffer, self._recv_buf))
                    return hdr
        else:
            print(f'emey read timeout')
            if not ignore_read_timeout:
                logger.error(f'Arduino serial port read timeout of {self.READ_TIMEOUT_SEC} '
                             f'seconds.')

#     def sample(self) -> Optional['Samples']:
#         try:
#             return Samples.from_buffer(self.execute(self.Level1Cmd.SAMPLE))
#         except (ValueError, TypeError):
#             logger.exception('Failed to cast sample data to structure.')
#         return None
#
# class Samples(ctypes.Structure):
#     # noinspection PyTypeChecker
#     _fields_ = [
#         ('data', ctypes.c_uint16 * ArduinoSerial.NUMBER_OF_CHANNELS)
#     ]
