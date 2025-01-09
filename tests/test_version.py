from unittest import TestCase

import growbies

class Test(TestCase):
    def test(self):
        self.assertTrue(hasattr(growbies, '__version__'))
