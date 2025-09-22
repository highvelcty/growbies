from unittest import TestCase

from growbies.utils import report

class Test(TestCase):
    def test_float_list_str_wrap(self):
        exp = """\
[123456.78, 123456.78, 123456.78, 123456.78,
 123456.78, 123456.78, 123456.78, 123456.78]"""
        vals = [123456.78 for _ in range(8)]
        vals = report.list_str_wrap(vals)
        self.assertEqual(exp, vals)