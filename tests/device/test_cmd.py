from unittest import TestCase

from growbies.device.common.identify import Identify1
from growbies.device.cmd import SetIdentifyDeviceCmd

class TestSetIdentifyDeviceCmd(TestCase):
    def test(self):
        test_model_name = 'test_model_name'
        identify = Identify1(model_number=test_model_name)

        cmd_ = SetIdentifyDeviceCmd(payload=identify)

        self.assertEqual(test_model_name, cmd_.payload.model_number)
