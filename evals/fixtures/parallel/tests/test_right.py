import unittest

from right import parse_limit


class LimitTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_limit("2"), 2)
