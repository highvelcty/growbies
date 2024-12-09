from unittest import TestCase

import precision_farming

class Test(TestCase):
    def test(self):
        self.assertTrue(hasattr(precision_farming, '__version__'))
