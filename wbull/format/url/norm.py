"""URL Normalization

This module provides methods to format URL components into a
consistent form.
"""

from wbull.format.url.encode import \
    uppercase_percent_encoding as _uppercase_percent_encoding, \
    percent_encode as _percent_encode, \
    percent_encode_plus as _percent_encode_plus, \
    FRAGMENT_ENCODE_SET as _FRAGMENT_ENCODE_SET, \
    USERNAME_ENCODE_SET as _USERNAME_ENCODE_SET, \
    PASSWORD_ENCODE_SET as _PASSWORD_ENCODE_SET
from wbull.format.url.path import flatten_path as _flatten_path


def normalize_hostname(hostname: str) -> str:
    """Normalizes a hostname so that it is ASCII and valid domain name.

    Raises:
        ValueError: The hostname cannot be formatted as a valid domain
            name.
    """
    new_hostname = hostname.encode('idna').decode('ascii').lower()

    # Fast path
    if hostname == new_hostname:
        return new_hostname

    # Check for round-trip. May raise UnicodeError
    new_hostname.encode('idna')

    return new_hostname


def normalize_path(path: str, encoding: str='utf-8', errors: str='strict'):
    """Normalize a path string.

    Flattens a path by removing dot segments, percent-encodes
    unacceptable characters, and ensures percent-encoding is uppercase.
    """
    return _uppercase_percent_encoding(
        _percent_encode(_flatten_path(path, flatten_slashes=True),
                        encoding=encoding, errors=errors)
    )


def normalize_query(text, encoding='utf-8', errors: str='strict'):
    """Normalize a query string.

    Percent-encodes unacceptable characters and ensures percent-encoding is
    uppercase.
    """
    return _uppercase_percent_encoding(
        _percent_encode_plus(text, encoding=encoding, errors=errors)
    )


def normalize_fragment(text, encoding='utf-8', errors: str='strict'):
    """Normalize a fragment.

    Percent-encodes unacceptable characters and ensures percent-encoding is
    uppercase.
    """
    return _uppercase_percent_encoding(
        _percent_encode(text, encoding=encoding,
                        encode_set=_FRAGMENT_ENCODE_SET, errors=errors)
    )


def normalize_username(text, encoding='utf-8', errors: str='strict'):
    """Normalize a username

    Percent-encodes unacceptable characters and ensures percent-encoding is
    uppercase.
    """
    return _uppercase_percent_encoding(
        _percent_encode(text, encoding=encoding,
                        encode_set=_USERNAME_ENCODE_SET, errors=errors)
    )


def normalize_password(text, encoding='utf-8', errors: str='strict'):
    """Normalize a password

    Percent-encodes unacceptable characters and ensures percent-encoding is
    uppercase.
    """
    return _uppercase_percent_encoding(
        _percent_encode(text, encoding=encoding,
                        encode_set=_PASSWORD_ENCODE_SET, errors=errors)
    )
