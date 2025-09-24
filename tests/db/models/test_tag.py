from unittest import TestCase

from growbies.db.models import tag

class Test(TestCase):
    def test_TagBuiltinName(self):
        descriptions = []
        for name in tag.BuiltinName:
            descriptions.append(name.description)
            # Make sure all tags have descriptions
            self.assertNotEqual('', name.description)
        # Check for description uniqueness
        self.assertEqual(len(descriptions), len(set(descriptions)))

