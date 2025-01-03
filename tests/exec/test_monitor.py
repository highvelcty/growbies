from pathlib import Path
from unittest import TestCase
from io import StringIO

from precision_farming.exec import monitor


PATH_TO_SAMPLES = Path(__file__).parent / 'samples'

class TestContinueFile(TestCase):
    def test_corrupted_data(self):
        path_to_corrupted_data = PATH_TO_SAMPLES / 'corrupt_monitor_data.csv'
        exp_str = """\
timestamp,channel0,channel1,channel2,channel3
2024-12-30T20:31:18.111926Z,559,295,862,442
2024-12-30T20:31:19.119862Z,559,295,862,442
"""
        data_stream = StringIO()
        with open(path_to_corrupted_data, 'r') as inf:
            data_stream.write(inf.read())

        monitor._continue_stream(data_stream)
        data_stream.seek(0)
        self.assertEqual(exp_str, data_stream.read())

    def test_corrupted_data2(self):
        path_to_corrupted_data = PATH_TO_SAMPLES / 'corrupt_monitor_data2.csv'
        exp_str = """\
timestamp,channel0,channel1,channel2,channel3
2024-12-30T20:31:18.111926Z,559,295,862,442
2024-12-30T20:31:19.119862Z,559,295,862,442
"""
        data_stream = StringIO()
        with open(path_to_corrupted_data, 'r') as inf:
            data_stream.write(inf.read())

        monitor._continue_stream(data_stream)
        data_stream.seek(0)
        print(data_stream.read())
        # self.assertEqual(exp_str, data_stream.read())