from abc import abstractmethod
from unittest import TestCase


class BaseMockArduino(object):
    def __init__(self, *args, **kw):
        self.written = b''

    def reset(self):
        self.written = b''

    def write(self, data):
        self.written += data

class BaseTest(TestCase):
    _arduino_serial = None

    @classmethod
    def setUpClass(cls):
        cls._arduino_serial = cls.make_mock_arduino()

    def setUp(self):
        self._arduino_serial.reset()

    @classmethod
    @abstractmethod
    def make_mock_arduino(cls):
        ...