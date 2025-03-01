from abc import abstractmethod
from typing import ByteString

import serial

from growbies.utils.bufstr import BufStr


class BaseArduinoSerial(object):
    DEBUG_DATALINK_READ = False
    DEBUG_DATALINK_WRITE = False

    def __init__(self, *args, port='/dev/ttyACM0', baudrate=115200, timeout=0.5, **kw):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        self._serial = serial.Serial(*args, port=port, baudrate=baudrate, timeout=timeout, **kw)
        self.wait_for_ready()

    @property
    def in_waiting(self) -> int:
        return self._serial.in_waiting

    def read(self, size=1) -> bytes:
        buf = self._serial.read(size)
        if self.DEBUG_DATALINK_READ: print(f'python datalink recv:\n{BufStr(buf)}')
        return buf

    def write(self, buf: ByteString):
        if self.DEBUG_DATALINK_WRITE: print(f'python datalink send:\n{BufStr(buf)}')
        self._serial.write(buf)

    @abstractmethod
    def wait_for_ready(self):
        ...
