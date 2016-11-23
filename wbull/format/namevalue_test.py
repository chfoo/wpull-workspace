import unittest

from wbull.format.namevalue import split_and_unfold_lines, NameValueRecord


class TestNameValue(unittest.TestCase):
    def test_split_and_unfold_lines(self):
        self.assertEqual(
            [
                'name1: hi',
                'name2: blah blah  blah\tblah',
                'name3: hello world'
            ],
            split_and_unfold_lines(
                'name1: hi\n'
                'name2: blah\r\n blah\r\n  blah\tblah\r\n'
                'name3: hello world'
            )
        )

        with self.assertRaises(ValueError):
            split_and_unfold_lines(' malformed\r\n')

    def test_name_value_setter_getters(self):
        record = NameValueRecord()

        self.assertNotIn('name1', record)

        record['Name1'] = 'Value1'

        self.assertIn('name1', record)
        self.assertIn('Name1', record)
        self.assertEqual('Value1', record['name1'])

        self.assertNotIn('name2-¤', record)
        record['Name2-¤'] = 'Value2'
        self.assertEqual('Value2', record['name2-¤'])

        self.assertEqual(2, len(record))
        self.assertEqual(['Name1', 'Name2-¤'], list(record  ))

        del record['name1']

        self.assertEqual(1, len(record))

        self.assertNotIn('name1', record)

    def test_name_value_list_aspect(self):
        record = NameValueRecord()

        record['Name1'] = 'Value1'
        record.add('name1', 'Value2')

        self.assertEqual('Value1', record['name1'])
        self.assertEqual(['Value1', 'Value2'], record.get_list('name1'))

        self.assertEqual(
            [('Name1', 'Value1'), ('Name1', 'Value2')],
            list(record.get_pairs())
        )

        record['Name1'] = 'Value3'

        self.assertEqual('Value3', record['name1'])
        self.assertEqual(['Value3'], record.get_list('name1'))

        del record['Name1']

        record.add('name1', 'Value4')

        self.assertEqual('Value4', record['name1'])
        self.assertEqual(['Value4'], record.get_list('name1'))

    def test_name_value_parse_mixed_line_ending(self):
        record = NameValueRecord()
        record.loads(
            'dog: woof\n'
            'cat: meow\r\n'
            'bird: tweet\r'
            'mouse: squeak\n'
            'cow: moo\r\n'
            'frog: croak\n\r'
            'elephant: toot\n'
            'duck: quack\r\n'
            'fish: blub\n'
            'seal: \r\n'
            ' ow ow ow\r'
            'fox: ???\r'
        )

        self.assertEqual('woof', record['dog'])
        self.assertEqual('meow', record['cat'])
        self.assertEqual('tweet', record['bird'])
        self.assertEqual('squeak', record['mouse'])
        self.assertEqual('moo', record['cow'])
        self.assertEqual('croak', record['frog'])
        self.assertEqual('toot', record['elephant'])
        self.assertEqual('quack', record['duck'])
        self.assertEqual('blub', record['fish'])
        self.assertEqual('ow ow ow', record['seal'])
        self.assertEqual('???', record['fox'])

    def test_name_value_parse_colon(self):
        record = NameValueRecord()
        record.loads(
            'no-colon\n'
            'name-only:\n'
            ': value-only\n'
            'spaces-around-colon  :value\n'
            'lots-of-colons : value1: value2 \n'
        )

        self.assertEqual('', record['no-colon'])
        self.assertEqual('', record['name-only'])
        self.assertEqual('value-only', record[''])
        self.assertEqual('value', record['spaces-around-colon'])
        self.assertEqual('value1: value2', record['lots-of-colons'])

    def test_name_value_serialize(self):
        record = NameValueRecord()
        record['Name1'] = 'hello world'
        record.add('Name2', 'value1')
        record.add('Name2', 'value2')

        self.assertEqual(
            'Name1: hello world\r\n'
            'Name2: value1\r\n'
            'Name2: value2\r\n',
            record.dumps()
        )

    def test_name_value_folding(self):
        record = NameValueRecord()
        record['Name1'] = 'hello world'
        record.add('Name2', 'value1')
        record.add('Name2', 'value2')

        self.assertEqual(
            'Name1: hello\r\n'
            ' world\r\n'
            'Name2: value1\r\n'
            'Name2: value2\r\n',
            record.dumps(fold_width=7)
        )
