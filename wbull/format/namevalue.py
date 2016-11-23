"""Name Value Records

Name-value records consists of a list of name-value pairs (also known as
key-value pairs) that typically accompany data known as a payload. This
module uses the well-known HTTP header format.

Name-value records are represented in plaintext with carriage return and
line feed separating each pair. (Although incorrect, this module will
accept single carriage return or line feed.) Names and values are
separated with a colon. Names are case-insensitive and can be
duplicated within the list. Values may be word folded or word-wrapped
on a new line by prefixing it with a space or horizontal tab. (Since
folding specifications differ among protocols, spaces may be mangled
and using folding should be avoided for machine-readable values.)
"""
import collections.abc
import io
import textwrap
from typing import Iterator, Tuple, List, Optional


class NameValueRecord(collections.abc.MutableMapping):
    """Mutable mapping of HTTP header style of name-value pairs.

    Names are case-insensitive, but in practice, the rule may be
    overlooked. To accommodate this issue, operations dealing with
    names are treated case-insensitive, but the names are stored with
    case preserved and will return untouched.

    Although names are typically unique in practice, there are cases
    where there may be duplicate names. For this purpose, additional
    methods such as `get_list` are provided.

    For simplicity and performance reasons, the list order of
    name-value pairs is not entirely preserved for duplicate names.

    Although invalid in some specifications, extra or missing spaces
    around colons and missing names or values are accepted by this
    class.
    """

    def __init__(self):
        # normalized_key: str -> dict(key: str, values: list)
        self._data = collections.OrderedDict()

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Returns the normalized name used for internal comparisons."""
        return name.strip().title()

    def __getitem__(self, key):
        return self._data[self.normalize_name(key)]['values'][0]

    def __setitem__(self, key, value):
        self._data[self.normalize_name(key)] = {'key': key, 'values': [value]}

    def __delitem__(self, key):
        del self._data[self.normalize_name(key)]

    def __iter__(self):
        for value_info in self._data.values():
            yield value_info['key']

    def __len__(self):
        return len(self._data)

    def loads(self, text: str):
        """Parse the given text and add the pairs."""
        for line in split_and_unfold_lines(text):
            name, partition, value = line.partition(':')
            name = name.strip()
            value = value.strip()
            self.add(name, value)

    def dumps(self, fold_width: Optional[int] = None) -> str:
        """Serialize the pairs as a string.

        Args:
            fold_width: The maximum length of a value before it is text
            wrapped.
        """
        buffer = io.StringIO()

        for name, value in self.get_pairs():
            buffer.write(name)
            buffer.write(': ')

            if fold_width:
                value_lines = textwrap.wrap(value, fold_width)
                buffer.write('\r\n '.join(value_lines))
            else:
                buffer.write(value)

            buffer.write('\r\n')

        return buffer.getvalue()

    def add(self, name: str, value: str):
        """Append a name-value pair to the record."""
        normalized_key = self.normalize_name(name)

        if normalized_key not in self._data:
            self._data[normalized_key] = {'key': name, 'values': [value]}
        else:
            self._data[normalized_key]['values'].append(value)

    def get_list(self, name: str) -> List[str]:
        """Return all the values for the given name."""
        return list(self._data[self.normalize_name(name)]['values'])

    def get_pairs(self) -> Iterator[Tuple[str, str]]:
        """Return all the name-value pairs."""

        for value_info in self._data.values():
            for value in value_info['values']:
                yield value_info['key'], value


def split_and_unfold_lines(text: str) -> List[str]:
    """Split given string into lines and unfold them."""
    lines = []
    for line in text.splitlines():
        if not line:
            continue
        if line[0] in ' \t':
            if not lines:
                raise ValueError('Cannot unfold line without existing line.')

            lines[-1] += line
        else:
            lines.append(line)

    return lines
