import unittest

from left import normalize_tag


class TagTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(normalize_tag("tag"), "tag")
