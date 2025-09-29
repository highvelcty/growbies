from unittest import TestCase

from growbies.db.models import session

class Test(TestCase):
    def test_construction(self):
        test_name = 'test_name'
        sess = session.Session(name=test_name)

        self.assertEqual(test_name, sess.name)
