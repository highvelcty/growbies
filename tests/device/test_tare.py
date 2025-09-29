from ctypes import sizeof
from unittest import TestCase

from growbies.device.common.tare import Tare, NvmTare

class Test(TestCase):
    def test(self):
        tare_list = [(0.0,1.0)]
        tare = Tare()
        existing = tare.values
        for idx, val in tare_list:
            existing[int(idx)] = val
        tare.values = existing

        self.assertAlmostEqual(tare.values[0], 1.0)

    def test_size(self):
        self.assertEqual(40, sizeof(NvmTare))
