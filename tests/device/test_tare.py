from unittest import TestCase

from growbies.device.common.tare import Tare

class Test(TestCase):
    def test(self):
        tare_list = [(0.0,1.0)]
        tare = Tare()
        existing = tare.values
        for idx, val in tare_list:
            existing[int(idx)] = val
        tare.values = existing

        self.assertAlmostEqual(tare.values[0], 1.0)

    def test2(self):
        buf = bytearray(b'\x00' * 6 + b'\x80\x3f' + (b'\x00' * 12))
        tare = Tare.from_buffer(buf)
        print(tare)
        print(tare.values[0])