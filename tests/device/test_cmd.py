from unittest import TestCase

from growbies.device.common.identify import Identify1
from growbies.device.cmd import SetIdentifyDeviceCmd

class TestSetIdentifyDeviceCmd(TestCase):
    def test(self):
        test_model_name = 'test_model_name'
        identify = Identify1(model_number=test_model_name)

        cmd = SetIdentifyDeviceCmd(identify=identify)

        self.assertEqual(test_model_name, cmd.identify.model_number)
        self.assertFalse(cmd.init)

    def test2(self):
        buf = bytearray(
            b'0.0.1-dev0+214bb15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )

        identify = Identify1.from_buffer(buf)
        cmd = SetIdentifyDeviceCmd()
        cmd.identify = identify
        self.assertEqual(bytes(identify), bytes(cmd.identify))
        self.assertFalse(cmd.init)
