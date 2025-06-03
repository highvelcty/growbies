from unittest import TestCase
from pathlib import Path

from growbies.utils.ftdi import get_usb_paths
from growbies.utils.firmware import make_upload_mini

class Test(TestCase):
    _device_paths: list[Path] = list()

    @classmethod
    def setUpClass(cls):
        cls._device_paths = list(get_usb_paths())


    def test_ftdi_found(self):
        self.assertTrue(self._device_paths)
        for path in self._device_paths:
            self.assertTrue(path.exists())


    def test_make_upload_mini(self):
        make_upload_mini()
