import unittest

from wbull.format.url.encode import percent_encode, percent_encode_plus, \
    percent_decode, percent_decode_plus, uppercase_percent_encoding, \
    percent_encode_query_value, percent_encode_query_key


class EncodeTestCase(unittest.TestCase):
    def test_percent_encode(self):
        self.assertEqual('a%20', percent_encode('a '))
        self.assertEqual('a%C3%B0%01', percent_encode('að\u0001'))

    def test_percent_encode_plus(self):
        self.assertEqual('a+', percent_encode_plus('a '))
        self.assertEqual('a%C3%B0%01', percent_encode_plus('að\u0001'))

    def test_percent_decode(self):
        self.assertEqual('a ', percent_decode('a%20'))
        self.assertEqual('að\u0001', percent_decode('a%C3%B0%01'))

    def test_percent_decode_plus(self):
        self.assertEqual('a ', percent_decode_plus('a+'))
        self.assertEqual('að\u0001', percent_decode_plus('a%C3%B0%01'))

    def test_percent_encode_query(self):
        self.assertEqual('a%26b%3D%2B', percent_encode_query_key('a&b=+'))
        self.assertEqual('a%26b=%2B', percent_encode_query_value('a&b=+'))

    def test_uppercase_percent_encoding(self):
        self.assertEqual(
            'ð',
            uppercase_percent_encoding('ð')
        )
        self.assertEqual(
            'qwerty%%asdf',
            uppercase_percent_encoding('qwerty%%asdf')
        )
        self.assertEqual(
            'cAt%2F%EE%AB%AB',
            uppercase_percent_encoding('cAt%2f%ee%Ab%aB')
        )