from enum import Enum
import logging
import time

import serial

logger = logging.getLogger(__name__)

class ArduinoSerial(serial.Serial):
    READY_TIMEOUT_SEC = 5
    READ_TIMEOUT = 1
    class Level1Cmd(Enum):
        LOOPBACK = 'loopback'
        SAMPLE = 'sample'

    def __init__(self):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        super().__init__(port='/dev/ttyACM0', baudrate=115200, timeout=0.5)

        self._wait_for_ready()

    def _wait_for_ready(self):
        """From experimentation and quick reading on the internet; it seems that opening a serial
        connection resets the arduino. It takes a few seconds for the arduino serial port to
        stabilize. This method will poll for readiness, blocking until ready or timeout."""
        startt = time.time()
        while time.time() - startt < self.READY_TIMEOUT_SEC:
            in_data = self.execute(self.Level1Cmd.LOOPBACK)
            if in_data.startswith(self.Level1Cmd.LOOPBACK.value.encode()):
                break
        else:
            raise TimeoutError(f'Arduino serial port not ready in {self.READY_TIMEOUT_SEC} seconds')


    def execute(self, cmd: 'Level1Cmd') -> bytes:
        if isinstance(cmd, self.Level1Cmd):
            out_data = (cmd.value + '\n').encode()
        else:
            out_data = (cmd + '\n').encode()
        logger.debug(f'Arduino serial out: {out_data}')
        self.write(out_data)
        startt = time.time()
        in_data = b''
        while time.time() - startt < self.READ_TIMEOUT:
            bytes_in_waiting = self.in_waiting
            if bytes_in_waiting:
                in_data += self.read(bytes_in_waiting)
                if in_data.endswith(b'\n'):
                    break

        # in_data = self.readline()
        logger.debug(f'Arduino serial in: {in_data}')
        return in_data

    def sample(self) -> list[int]:
        data = []
        data_str = self.execute(self.Level1Cmd.SAMPLE).decode().strip()
        try:
            data = [int(val) for val in data_str.split(',')]
        except ValueError:
            logger.exception(f'Failed to convert samples to ints. Received string: "{data_str}"')
        return data
