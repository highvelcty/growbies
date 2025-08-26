from abc import ABC
from typing import ByteString
import logging

import serial

from growbies.utils.bufstr import BufStr

logger = logging.getLogger(__name__)

class BaseSerial(ABC):
    DEBUG_DATALINK_READ = True
    DEBUG_DATALINK_WRITE = True

    def __init__(self, *args, port='/dev/ttyACM0', baudrate=57600, timeout=0.5, **kw):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        self._serial = serial.Serial(*args, port=port, baudrate=baudrate, timeout=timeout, **kw)

    def close(self):
        self._serial.close()

    def reset_input_buffer(self):
        self._serial.reset_input_buffer()

    def reset_output_buffer(self):
        self._serial.reset_output_buffer()

    @property
    def in_waiting(self) -> int:
        return self._serial.in_waiting

    def fileno(self) -> int:
        return self._serial.fileno()

    def read(self, size=1) -> bytes:
        buf = self._serial.read(size)
        if self.DEBUG_DATALINK_READ: logger.debug(f'python datalink recv:\n{BufStr(buf)}')
        return buf

    def write(self, buf: ByteString):
        if self.DEBUG_DATALINK_WRITE: logger.debug(f'python datalink send:\n{BufStr(buf)}')
        self._serial.write(buf)
