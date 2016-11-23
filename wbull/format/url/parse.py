"""URL parsing

"""
import ipaddress
from typing import List, Optional, Tuple, Iterable
import re

from wbull.format.url.encode import \
    percent_decode as _percent_decode, \
    percent_decode_plus as _percent_decode_plus, \
    percent_encode as _percent_encode, \
    percent_encode_plus as _percent_encode_plus, \
    percent_encode_query_key as _percent_encode_query_key, \
    percent_encode_query_value as _percent_encode_query_value, \
    PASSWORD_ENCODE_SET as _PASSWORD_ENCODE_SET, \
    USERNAME_ENCODE_SET as _USERNAME_ENCODE_SET, \
    C0_CONTROL_SET as _C0_CONTROL_SET, \
    FORBIDDEN_HOSTNAME_CHARS as _FORBIDDEN_HOSTNAME_CHARS
from wbull.format.url.norm import \
    normalize_hostname as _normalize_hostname, \
    normalize_path as _normalize_path, \
    normalize_query as _normalize_query

RELATIVE_SCHEME_DEFAULT_PORTS = {
    'ftp': 21,
    'gopher': 70,
    'http': 80,
    'https': 443,
    'ws': 80,
    'wss': 443,
}


class URLInfo:
    """Parse and manipulate parts of a URL.

    Attributes:
        scheme (str): Protocol such as HTTPS or FTP in lowercase.
        hostname (str, optional): Domain in ASCII or IP address. If IPv6
            address, the brackets are omitted.
        port (int, optional): Port number for networking.
        encoding (str): Name of encoding for string encoding as in
            ``str.encode``.
        query_encoding (str): Name of encoding for the query portion
            as in ``str.encode``.
        errors (str): String encoding error handling as in
            ``str.encode``.
        username (str, optional): Username of user supplied
            credentials.
        password (str, optional): Password of user supplied
            credentials.
        path (str, optional): Path portion of URL. The leading slash
            is included. The path is percent-encoded.
        query (str, optional): Query portion of the URL. The leading
            question mark is omitted. The query is percent-encoded.
        fragment (str, optional): Fragment portion of the URL. The
            leading hash symbol is omitted. The fragment is
            intentionally not percent-encoded.
        address (ipaddress.IPv4Address, optional): IP address.

    When setting values, they will automatically be percent-encoded
    where appropriate.

    URL parsing is similar to WHATWG URL living standard.

    For more information about how the URL parts are derived, see
    https://medialize.github.io/URI.js/about-uris.html
    """

    def __init__(self,
                 scheme: str,
                 hostname: Optional[str]=None,
                 port: Optional[int]=None,
                 path: Optional[str]=None,
                 encoding: str='utf-8',
                 query_encoding: str='utf-8',
                 errors: str='strict'
                 ):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.encoding = encoding
        self.query_encoding = query_encoding
        self.errors = errors
        self.username = None
        self.password = None
        self.path = path
        self.query = None
        self.fragment = None
        self.address = None

    @property
    def origin(self) -> str:
        """Formatted string of scheme and authority.

        Example: ``http://user:pass@example.com:8080``
        """
        if self.host:
            return '{}://{}'.format(self.scheme, self.authority)
        else:
            return '{}:{}'.format(self.scheme, self.authority)

    @origin.setter
    def origin(self, new_origin: str):
        self.scheme, self.authority = self.parse_origin(new_origin)

    @property
    def authority(self) -> str:
        """Formatted string of userinfo and host.

        Example: ``user:pass@example.com:8080``

        Userinfo may be omitted if it is empty.
        """
        if self.userinfo:
            return '{}@{}'.format(self.userinfo, self.host)
        else:
            return self.host

    @authority.setter
    def authority(self, new_authority: str):
        self.userinfo, self.host = self.parse_authority(new_authority)

    @property
    def userinfo(self) -> str:
        """Formatted string of username and password.

        Example: ``user:pass``
        """
        if self.username or self.password:
            return '{}{}{}'.format(
                _percent_encode(self.username or '', _USERNAME_ENCODE_SET),
                ':' if self.password else '',
                _percent_encode(self.password or '', _PASSWORD_ENCODE_SET)
            )
        else:
            return ''

    @userinfo.setter
    def userinfo(self, new_userinfo: str):
        self.username, self.password = self.parse_userinfo(new_userinfo)
        self.username = _percent_decode(
            self.username, encoding=self.encoding, errors=self.errors
        )
        self.password = _percent_decode(
            self.password, encoding=self.encoding, errors=self.errors
        )

    @property
    def host(self) -> str:
        """Formatted string of hostname and port.

        Example: ``example.com:8080``

        Port may be omitted if the port number is the default for the
        currently set scheme. Hostname may be an IP address.
        """
        hostname = self.hostname
        port_str = ''

        if not self.hostname:
            return ''

        if self.is_ipv6:
            hostname = '[{}]'.format(hostname)

        if self.port and RELATIVE_SCHEME_DEFAULT_PORTS[self.scheme] != self.port:
            port_str = ':{}'.format(self.port)

        return hostname + port_str

    @host.setter
    def host(self, new_host: str):
        (self.hostname, self.address), self.port = self.parse_host(new_host)

        if not self.port:
            self.port = RELATIVE_SCHEME_DEFAULT_PORTS.get(self.scheme)

    @property
    def resource(self) -> str:
        """Formatted string of path, query, and fragment.

        Example: ``/blog.php?id=123#photo5``

        Query and fragment may be omitted if they are empty.
        """
        path = self.path or '/'
        parts = [path]

        if self.scheme in RELATIVE_SCHEME_DEFAULT_PORTS and path[0] != '/':
            parts.insert(0, '/')

        if self.query:
            parts.append('?')
            parts.append(_percent_encode_plus(
                self.query, encoding=self.query_encoding, errors=self.errors)
            )

        if self.fragment:
            parts.append('#')
            parts.append(self.fragment)

        return ''.join(parts)

    @resource.setter
    def resource(self, new_resource: str):
        self.path, self.query, self.fragment = self.parse_resource(new_resource)
        self.path = _normalize_path(
            self.path, encoding=self.encoding, errors=self.errors
        )
        self.query = _normalize_query(
            self.query, encoding=self.query_encoding, errors=self.errors
        )

    @property
    def url(self) -> str:
        """Fully formatted URL."""
        return '{}{}'.format(self.origin, self.resource)

    def geturl(self, defrag: bool=False) -> str:
        """Return formatted URL.

        Args:
            defrag: Whether to remove the fragment.

        If no parameters are specified, a fully formatted URL is
        returned by default.
        """

    @property
    def is_ipv6(self) -> bool:
        """Whether the hostname is an IPv6 address."""
        return self.address and self.address.version == 6 or ':' in self.hostname

    @classmethod
    def parse(cls, url: str, default_scheme='http', encoding='utf-8',
              query_encoding='utf-8', errors='strict') \
            -> 'URLInfo':
        """Parse the URL.

        Args:
            url: The URL. The scheme may be omitted and a default is
                assumed.
            default_scheme: THe scheme to be used when a scheme cannot
                be detected.
            encoding: The encoding to use when escaping characters
                with percent-encoding as in ``str.encode``.
            query_encoding: The encoding to use for the query portion
                as in ``str.encode``.
            errors: The encoding error handling as in ``str.encode``.
        """
        url = url.strip()
        if frozenset(url) & _C0_CONTROL_SET:
            raise ValueError('URL contains control codes: {}'.format(ascii(url)))

        scheme, sep, remaining = url.partition(':')

        if not scheme:
            raise ValueError('URL missing scheme: {}'.format(ascii(url)))

        scheme = scheme.lower()

        if not sep and default_scheme:
            # Likely something like example.com/mystuff
            remaining = url
            scheme = default_scheme
        elif not sep:
            raise ValueError('URI missing colon: {}'.format(ascii(url)))

        if default_scheme and '.' in scheme or scheme == 'localhost':
            # Maybe something like example.com:8080/mystuff or
            # maybe localhost:8080/mystuff
            remaining = '{}:{}'.format(scheme, remaining)
            scheme = default_scheme

        info = URLInfo(scheme)
        info.encoding = encoding
        info.query_encoding = query_encoding
        info.errors = errors

        if scheme not in RELATIVE_SCHEME_DEFAULT_PORTS:
            info.raw = url
            info.scheme = scheme
            info.path = remaining

            return info

        match = re.match(r'/*(.*?)($|[/?#].*)', remaining)

        authority = match.group(1)
        resource = match.group(2)

        info.authority = authority
        info.resource = resource

        return info

    @classmethod
    def parse_origin(cls, origin: str) -> tuple:
        """Return scheme and authority from origin string."""
        scheme, authority = re.match('(.+?):/{0,2}(.*)', origin).groups()

        scheme = scheme.lower()

        return scheme, authority

    @classmethod
    def parse_authority(cls, authority: str) -> tuple:
        """Return userinfo and host from authority string."""
        userinfo, sep, host = authority.partition('@')

        if not sep:
            return '', userinfo
        else:
            return userinfo, host

    @classmethod
    def parse_userinfo(cls, userinfo: str) -> tuple:
        """Return username and password from userinfo string."""
        username, sep, password = userinfo.partition(':')

        return username, password

    @classmethod
    def parse_host(cls, host) -> tuple:
        """Return hostname and port number."""
        if host.endswith(']'):
            # IPv6 but no port number. Handle this case here to avoid
            # splitting on wrong colon.
            return cls.parse_hostname(host), None
        else:
            hostname, sep, port = host.rpartition(':')

        if sep:
            port = int(port)
            if port < 0 or port > 65535:
                raise ValueError('Port number invalid')
        else:
            hostname = port
            port = None

        return cls.parse_hostname(hostname), port

    @classmethod
    def parse_hostname(cls, hostname: str) \
            -> Tuple[str, Optional[ipaddress.IPv4Address]]:
        """Return a normalized hostname and optional IP Address."""
        if hostname.startswith('['):
            return cls.parse_ipv6_hostname(hostname)

        if not hostname:
            raise ValueError('Empty hostname')

        try:
            address = parse_ipv4_address(hostname)
            return address.compressed, address
        except ValueError:
            pass

        new_hostname = _normalize_hostname(hostname)

        if any(char in new_hostname for char in _FORBIDDEN_HOSTNAME_CHARS):
            raise ValueError('Invalid hostname: {}'
                             .format(ascii(hostname)))

        return new_hostname, None

    @classmethod
    def parse_ipv6_hostname(cls, hostname: str) -> ipaddress.IPv6Address:
        """Parse hostname string and return IPv6 address.

        Args:
            hostname: An IPv6 address string with brackets.
        """
        if not hostname.startswith('[') or not hostname.endswith(']'):
            raise ValueError('Invalid IPv6 address: {}'
                             .format(ascii(hostname)))

        address = ipaddress.IPv6Address(hostname[1:-1])

        return address.compressed, address

    @classmethod
    def parse_resource(cls, resource: str) -> tuple:
        """Return path, query, and fragment from resource string."""
        match = re.match(r'(.*?)($|[#?])(.*)', resource)

        path = match.group(1)
        sep = match.group(2)
        remain = match.group(3)

        if sep == '?':
            query, sep, fragment = remain.partition('#')
        elif sep == '#':
            query = ''
            fragment = remain
        else:
            query = ''
            fragment = ''

        return path, query, fragment


def schemes_similar(scheme1: str, scheme2: str) -> bool:
    """Return whether URL schemes are similar.

    This function considers the following schemes to be similar:

    * HTTP and HTTPS

    """
    if scheme1 == scheme2:
        return True

    scheme1 = scheme1.lower()
    scheme2 = scheme2.lower()

    if scheme1 in ('http', 'https') and scheme2 in ('http', 'https'):
        return True

    return False


def split_query(qs: str, keep_blank_values: bool=False,
                decode_escape: bool=True, encoding: str='utf-8',
                errors: str='strict') -> List[tuple]:
    """Split the query string into item pairs.

    Args:
        qs: The query string text to be processed.
        keep_blank_values: Whether to include items where the value
            is empty. If False, then the item is omitted completely.
        decode_escape: Whether to replace percent-encoding and plus
            sign with their unencoded characters.
        encoding: The encoding of the text that is percent-encoded
            as in `str.decode`.
        errors: The error handling as in `str.decode`.

    If blank values is kept, then the value portion of the item will
    have two specific Python values. If an equal sign (``=``) is
    present when splitting items, the value will be an empty string
    (``''``). Otherwise, the value will be ``None``. For example::

        >>> list(split_query('a=&b', keep_blank_values=True))
        [('a', ''), ('b', None)]
    """
    items = []
    for pair in qs.split('&'):
        name, delim, value = pair.partition('=')

        if decode_escape:
            name = _percent_decode_plus(name, encoding=encoding, errors=errors)
            value = _percent_decode_plus(value, encoding=encoding, errors=errors)

        if not delim and keep_blank_values:
            value = None

        if keep_blank_values or value:
            items.append((name, value))

    return items


def join_query(query_list: Iterable) -> str:
    """Join a list of item pairs into a query string.

    If the value is `None`, then the equal sign is not included
    in the string. Otherwise, including the empty string, the equal
    sign is included.

    The leading question mark is not included.

    Percent-encoding is applied to the result.
    """
    parts = []
    for key, value in query_list:
        key = _percent_encode_query_key(key)

        if value is not None:
            value = _percent_encode_query_value(value)
            parts.append('{}={}'.format(key, value))
        else:
            parts.append(key)

    return '&'.join(parts)


def parse_ipv4_int(text: str) -> int:
    """Parse an integer string representation of an IPv4 address.

    Accepts

        * hex ``0x1``
        * octal ``01``
        * decimal ``1``
    """
    if text.startswith('0x'):
        base = 16
    elif text.startswith('0'):
        base = 8
    else:
        base = 10

    return int(text, base)


def parse_ipv4_address(address: str) -> ipaddress.IPv4Address:
    """Parse an IPv4 address string.

    The intended use is to handle uncommon integer notations in
    decimal, hex, or octal formats rather than the common dotted quad
    format.
    """

    try:
        # Fast path
        return ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError:
        pass

    parts = address.split('.')

    if len(parts) == 4:
        total = 0

        for index, part in enumerate(parts):
            part_value = parse_ipv4_int(part)

            if part_value < 0 or part_value > 255:
                raise ValueError('Octet not in range in {}.'.format(address))

            total += part_value << (24 - index * 8)

        return ipaddress.IPv4Address(total)

    elif len(parts) == 1:
        return ipaddress.IPv4Address(parse_ipv4_int(address))
    else:
        raise ValueError('Not an IPv4 address')