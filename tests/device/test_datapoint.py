from unittest import TestCase
from growbies.device.common.read import DataPoint, EndpointType

class Test(TestCase):
    def test_unknown_endpoint(self):
        buf = bytearray(b'\xfe\x01\x00\xfd\x01\x00')
        datapoint = DataPoint(buf)
        self.assertEqual(2, len(datapoint.endpoints[EndpointType.UNKNOWN]))
        for entry in datapoint.endpoints[EndpointType.UNKNOWN]:
            self.assertEqual(3, len(entry))
            self.assertTrue(isinstance(entry, bytearray))

    def test_output(self):
        exp = \
r"""+------------------------------------+
|                Mass                |
+----------------+----------+--------+
| Total Mass (g) | Sensor 0 | Errors |
+----------------+----------+--------+
|    78542.46    | 78542.46 |   0    |
+----------------+----------+--------+
+-----------------------------------+
|            Temperature            |
+---------------+----------+--------+
| Avg Temp (°C) | Sensor 0 | Errors |
+---------------+----------+--------+
|     14.22     |  14.22   |   0    |
+---------------+----------+--------+
Unknown Endpoints:
    b'\xfe\x01\x00'"""
        buf = bytearray(b'\x02\x01\x00\x00\x04\x3b\x67\x99\x47\x05\x01\x00\x03\x04\x7a\x82'
                        b'\x63\x41\01\x04\x3b\x67\x99\x47\x04\x04\x7a\x82\x63\x41\xFE\x01\x00')
        datapoint = DataPoint(buf)
        self.assertEqual(exp, str(datapoint))
