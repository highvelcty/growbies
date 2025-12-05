from unittest import TestCase

from growbies.db.models.common import BuiltinTagName

class Test(TestCase):
    def test_TagBuiltinName(self):
        descriptions = []
        for name in BuiltinTagName:
            descriptions.append(name.description)
            # Make sure all tags have descriptions
            self.assertNotEqual('', name.description)
        # Check for description uniqueness
        self.assertEqual(len(descriptions), len(set(descriptions)))
