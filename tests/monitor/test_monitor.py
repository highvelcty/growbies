from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock
from tempfile import NamedTemporaryFile

from growbies.monitor import monitor
from growbies.session import Session


PATH_TO_SAMPLES = Path(__file__).parent / 'samples'

class TestContinueFile(TestCase):
    _tmp_file: NamedTemporaryFile = None
    _path_to_tmp_file = None

    @classmethod
    def setUpClass(cls):
        cls._tmp_file = NamedTemporaryFile('w')
        cls._path_to_tmp_file = Path(cls._tmp_file.name)

        with (open(PATH_TO_SAMPLES / 'corrupt_monitor_data.csv', 'r') as inf,
              open(cls._path_to_tmp_file, 'w') as outf):
            outf.write(inf.read())

    @classmethod
    def tearDownClass(cls):
        cls._tmp_file.close()

    def test_corrupted_data(self):
        exp_str = """\
timestamp,channel0,channel1,channel2,channel3
2024-12-30T20:31:18.111926Z,559,295,862,442
2024-12-30T20:31:19.119862Z,559,295,862,442
"""
        sess = Mock(Session)()
        sess.path_to_data = self._path_to_tmp_file
        monitor._continue_stream(sess)
        with open(self._path_to_tmp_file, 'r') as inf:
            inf_data = inf.read()
            self.assertEqual(exp_str, inf_data)

