from ctypes import sizeof
from unittest import TestCase

from packaging.version import Version

from growbies.device.common.identify import Identify1, NvmIdentify
from growbies.device.cmd import SetIdentifyDeviceCmd

class TestSetIdentifyDeviceCmd(TestCase):
    def test(self):
        test_model_name = 'test_model_name'
        identify = NvmIdentify()
        identify.payload.model_number = test_model_name

        cmd = SetIdentifyDeviceCmd(identify=identify)

        self.assertEqual(test_model_name, cmd.identify.payload.model_number)
        self.assertFalse(cmd.init)

    def test2(self):
        buf = bytearray(
            b'0.0.1-dev0+214bb15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )

        identify = Identify1.from_buffer(buf)
        cmd = SetIdentifyDeviceCmd()
        cmd.payload = identify
        self.assertEqual(bytes(identify), bytes(cmd.payload))
        self.assertFalse(cmd.init)

class TestNvmIdentify(TestCase):
    def test(self):
        buf = bytearray(b'\x01\x00i\xe0o\x00\x00\x000.0.1-dev0+6266bd2\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

        resp = NvmIdentify.from_buffer(buf)
        self.assertEqual(Version('0.0.1-dev0+6266bd2'), resp.payload.firmware_version)
        self.assertEqual(57449, resp.hdr.crc)
        self.assertEqual(1, resp.hdr.version)

    def test_construction(self):
        ident = NvmIdentify()
        self.assertEqual(ident.VERSION, ident.hdr.version)
        self.assertEqual(sizeof(ident.payload), ident.hdr.length)
