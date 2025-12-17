from unittest import TestCase
from growbies.device.common.read import DataPoint

class Test(TestCase):
    def test_unknown_endpoint(self):
        buf = bytearray(b'\xfe\x01\x00\xfd\x01\x00')
        datapoint = DataPoint(buf)
        self.assertEqual(2, len(datapoint.unknown))
        for entry in datapoint.unknown:
            self.assertEqual(3, len(entry))
            self.assertTrue(isinstance(entry, bytearray))

    def test_output(self):
        exp = \
r"""+-------------------------------------------------+
|                    DataPoint                    |
+--------------------------+----------------------+
| Field                    | Value                |
+--------------------------+----------------------+
| Timestamp                | 1970-01-01T00:00:00Z |
| Mass (g)                 | 78542.46             |
| Mass Sensors (ADC)       | [78542.46]           |
| Mass Errors              | [0]                  |
| Tare                     | []                   |
| Temperature (*C)         | 14.22                |
| Temperature Sensors (*C) | [14.22]              |
| Temperature Errors       | [0]                  |
+--------------------------+----------------------+
Unknown Endpoints:
    b'\xfe\x01\x00'"""


        buf = bytearray(b'\x02\x01\x00\x00\x04\x3b\x67\x99\x47\x05\x01\x00\x03\x04\x7a\x82'
                        b'\x63\x41\01\x04\x3b\x67\x99\x47\x04\x04\x7a\x82\x63\x41\xFE\x01\x00')
        datapoint = DataPoint(buf, timestamp=0)
        self.assertEqual(exp, str(datapoint))
