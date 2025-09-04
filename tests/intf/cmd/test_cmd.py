from unittest import TestCase

from growbies.intf.common.identify import *
from growbies.intf.cmd import *


class TestSetIdentifyDeviceCmd(TestCase):
    def test(self):
        test_model_name = 'test_model_name'
        identify = Identify1(model_number=test_model_name)
        identify._hdr._version = 1

        cmd_ = SetIdentifyDeviceCmd(payload=identify)

        self.assertEqual(1, cmd_.payload.hdr.version)
        self.assertEqual(test_model_name, cmd_.payload.model_number)
