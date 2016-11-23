"""URL Percent-Encoding

URL percent encoding, also known as quoting in the builtin library,
replaces reserved characters with escaped notation.

This module provides more flexible routines for percent-encoding than
the builtin library.
"""

import collections
import functools
import re
import urllib.parse


C0_CONTROL_SET = frozenset(chr(i) for i in range(0, 0x1f + 1))
"""Set of forbidden bytes (0x00 to 0x1f inclusive)."""

DEFAULT_ENCODE_SET = frozenset(b' "#<>?`')
"""Default set of ASCII-printable bytes that require percent-encoding.

This set is defined by WHATWG URL living standard.
It does not include 0x00 to 0x1F nor 0x1F or above.
"""

PASSWORD_ENCODE_SET = frozenset(DEFAULT_ENCODE_SET | frozenset(b'/@\\'))
"""Encoding set for passwords."""

USERNAME_ENCODE_SET = frozenset(PASSWORD_ENCODE_SET | frozenset(b':'))
"""Encoding set for usernames."""

QUERY_ENCODE_SET = frozenset(b'"#<>`')
"""Encoding set for query string of a URL.

This set does not include 0x20 (space) so it can be replaced with
0x43 (plus sign) later.
"""

FRAGMENT_ENCODE_SET = frozenset(b' "<>`')
"""Encoding set for fragment."""

QUERY_KEY_ENCODE_SET = frozenset(QUERY_ENCODE_SET | frozenset(b'&+%='))
"""Encoding set for a query key."""

QUERY_VALUE_ENCODE_SET = frozenset(QUERY_ENCODE_SET | frozenset(b'&+%'))
"""Encoding set for a query value."""

FORBIDDEN_HOSTNAME_CHARS = frozenset('#%/:?@[\\] ')
"""Set of forbidden hostname characters.

Does not include non-printing characters. Meant for ASCII.
"""


class PercentEncoderMap(collections.defaultdict):
    # This class is based on urllib.parse.Quoter
    def __init__(self, encode_set: frozenset):
        """Helper map for percent-encoding.

        Maps raw bytes to encoded bytes.

        Args:
            encode_set: A set of bytes that require encoding. Bytes
                from 0x00 to 0x1F and 0x7F above are already escaped by
                default and do not need to be included in this
                argument.
        """
        super().__init__()
        self.encode_set = encode_set

    def __missing__(self, char: int):
        if char < 0x20 or char > 0x7E or char in self.encode_set:
            result = '%{:02X}'.format(char).encode('ascii')
        else:
            result = bytes((char,))
        self[char] = result
        return result


_percent_encoder_map_cache = {}  # Set of bytes -> PercentEncoderMap instance


def _get_percent_encoder_map(encode_set: frozenset) -> PercentEncoderMap:
    try:
        return _percent_encoder_map_cache[encode_set]
    except KeyError:
        mapper = PercentEncoderMap(encode_set)
        _percent_encoder_map_cache[encode_set] = mapper
        return mapper


def percent_encode_bytes(data: bytes,
                         encode_set: frozenset=DEFAULT_ENCODE_SET) -> bytes:
    """Percent-encode control bytes and restricted bytes.

    Args:
        data: The byte string to be processed.
        encode_set: The set of bytes that should be
            replaced in addition to the control characters.
            This is set can be considered a blacklist of
            special characters.

    Unlike Python's builtin ``quote`` function, this function accepts
    a blacklist of special characters instead of a whitelist of safe
    characters to preserve as much as the original string.

    The control bytes are from 0x00 to 0x1F and 0x7F to 0xFF.
    """
    mapping_func = _get_percent_encoder_map(encode_set).__getitem__
    return b''.join(mapping_func(char) for char in data)


def percent_encode(text: str, encode_set: frozenset=DEFAULT_ENCODE_SET,
                   encoding: str='utf-8', errors: str='strict') -> str:
    """Percent-encode text.

    Args:
        text: The string to be encoded.
        encode_set: The set of bytes to be replaced.
        encoding: The encoding to use when converting the string to
            bytes for percent-encoding as in `str.encode`.
        errors: The error handling as in `str.encode`.

    By default, the encoding set is suitable for encoding the path
    portion of a URL.

    In HTML documents, the encoding should always be UTF-8 regardless
    of the document encoding except in the query string. For example
    in Windows-1252,
    ``https://example.com/&ouml;/?&ouml;`` should be encoded as
    ``https://example.com/%C3%B6/?%F6``.

    :see_also: :func:`percent_encode_bytes`.
    """
    data = text.encode(encoding, errors=errors)
    return percent_encode_bytes(data, encode_set).decode('ascii')


def percent_encode_plus(text: str, encoding_set: frozenset=QUERY_ENCODE_SET,
                        encoding: str='utf-8', errors: str='strict') -> str:
    """Percent-encode text for query strings.

    :see_also: :func:`percent_encode`.
    """
    return percent_encode(text, encoding_set, encoding, errors).replace(' ', '+')


percent_encode_query_key = functools.partial(
    percent_encode_plus, encoding_set=QUERY_KEY_ENCODE_SET
)
percent_encode_query_value = functools.partial(
    percent_encode_plus, encoding_set=QUERY_VALUE_ENCODE_SET
)

percent_decode = urllib.parse.unquote
percent_decode_plus = urllib.parse.unquote_plus


def uppercase_percent_encoding(text: str) -> str:
    """Replaces any lowercase percent-encoded sequences with uppercase."""
    return re.sub(
        r'%[a-fA-F0-9][a-fA-F0-9]',
        lambda match: match.group(0).upper(),
        text
    )
