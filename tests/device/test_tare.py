from ctypes import sizeof
from unittest import TestCase

from growbies.device.common.tare import NvmTare

class Test(TestCase):
    def test_size(self):
        self.assertEqual(104, sizeof(NvmTare))
