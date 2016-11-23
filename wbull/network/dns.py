"""DNS Resolution

This module provides a low level and platform-independent interface
to DNS resolution. It avoids using the OS DNS resolver system to ensure
it gets DNS queries and responses that are not mangled. Avoiding the
OS resolver is a known practice by modern browsers that must handle
invalid but usable DNS records. For example, user-provided subdomain
names in blog sites may contain spec violations.

As well, this module provides convenient methods to records from DNS
responses.
"""
import abc
import contextlib
import datetime
import enum
import random
import socket
from typing import Optional, List, NamedTuple, Iterable, Tuple

import asyncio
import dns.resolver
import itertools

import functools

from wbull.exceptions import DNSNotFound, NetworkTimeoutError
import wbull.util


AddressInfo = NamedTuple(
    'AddressInfo', [
        ('family', int),
        ('ip_address', str),
        ('sockaddr_extra', tuple)
    ])
"""Socket IP address details."""


_DNSRecordInfo = NamedTuple(
    '_DNSRecordInfo', [
        ('fetch_date', datetime.datetime),
        ('resource_records', List[dns.rrset.RRset])
    ])


class DNSRecordInfo(_DNSRecordInfo):
    """DNS resource records."""
    __slots__ = ()

    def to_text_format(self) -> str:
        """Format as detached DNS information as text."""
        return '\n'.join(itertools.chain(
            (self.fetch_date.strftime('%Y%m%d%H%M%S'), ),
            (rr.to_text() for rr in self.resource_records),
            (),
        ))


@enum.unique
class IPFamilyPreference(enum.Enum):
    """IPv4 and IPV6 preferences."""

    any = 'any'
    ipv4_only = socket.AF_INET
    ipv6_only = socket.AF_INET6


class ResolverResult:
    def __init__(self, addresses: Iterable[AddressInfo],
                 dns_records: Optional[Iterable[DNSRecordInfo]]=None):
        """DNS resolver results.

        Args:
            addresses: Socket addresses.
            dns_records: DNS resource records.
        """
        self._address_infos = list(addresses)
        self._dns_record_infos = tuple(dns_records) if dns_records else ()

    @property
    def addresses(self) -> List[AddressInfo]:
        """The IP addresses."""
        return self._address_infos

    @property
    def dns_records(self) -> Tuple[DNSRecordInfo]:
        """The DNS resource records."""
        return self._dns_record_infos

    @property
    def first(self) -> AddressInfo:
        """The first IP address result."""
        return self._address_infos[0]

    @property
    def first_ipv4(self) -> Optional[AddressInfo]:
        """The first IPv4 address."""
        for info in self._address_infos:
            if info.family == socket.AF_INET:
                return info

    @property
    def first_ipv6(self) -> Optional[AddressInfo]:
        """The first IPv6 address."""
        for info in self._address_infos:
            if info.family == socket.AF_INET6:
                return info

    def shuffle(self):
        """Shuffle the addresses."""
        random.shuffle(self._address_infos)

    def rotate(self):
        """Move the first address to the last position."""
        item = self._address_infos.pop(0)
        self._address_infos.append(item)


class BaseResolver(metaclass=abc.ABCMeta):
    def __init__(self,
                 family_preference: IPFamilyPreference=IPFamilyPreference.any,
                 bind_address: Optional[str]=None):
        """Base class for DNS resolvers.

        Args:
            family_preference: Filtering of IPv4 and IPv6 addresses.
            bind_address: The network interface to use when making
                requests to the network. This option will have no
                effect if requests are done outside the library such
                as ``getaddrinfo``.
        """
        self._family_preference = family_preference
        self._bind_address = bind_address

    @abc.abstractmethod
    async def resolve(self, host: str, timeout: Optional[float]=None) \
            -> ResolverResult:
        """Resolve a hostname to IP address.

        Args:
            host: The hostname to resolve.
            timeout: Time in seconds before `NetworkTimeoutError` is raised.
        """


class OSResolver(BaseResolver):
    """DNS resolver that uses getaddrinfo.

    This resolver will use the OS' DNS resolver. The OS' resolver may
    include extra results from internal networks or filter out results
    from DNS servers.
    """

    DNS_NX_ERRNO = (socket.EAI_FAIL, socket.EAI_NODATA, socket.EAI_NONAME)
    SOCKET_FAMILY_MAP = {
        IPFamilyPreference.any: socket.AF_UNSPEC,
        IPFamilyPreference.ipv4_only: socket.AF_INET,
        IPFamilyPreference.ipv6_only: socket.AF_INET6,
    }

    async def resolve(self, host: str, timeout: Optional[float]=None) -> ResolverResult:
        family = self.SOCKET_FAMILY_MAP[self._family_preference]

        event_loop = asyncio.get_event_loop()
        query = event_loop.getaddrinfo(host, 0, family=family,
                                       proto=socket.IPPROTO_TCP)

        try:
            with self._reraise_dns_error():
                results = await asyncio.wait_for(query, timeout)
        except asyncio.TimeoutError as error:
            raise NetworkTimeoutError('DNS resolve timed out.') from error
        else:
            return ResolverResult(list(self._convert_os_results(results)))

    @classmethod
    @contextlib.contextmanager
    def _reraise_dns_error(cls):
        try:
            yield
        except socket.error as error:
            if error.errno in cls.DNS_NX_ERRNO:
                raise DNSNotFound(
                    'DNS resolution failed: {error}'.format(error=error)
                ) from error
            else:
                raise ConnectionError(
                    'DNS resolution error: {error}'.format(error=error)
                ) from error

    @classmethod
    def _convert_os_results(cls, results: list) -> Iterable[AddressInfo]:
        for family, type, proto, canonname, sockaddr in results:
            host, *extra = sockaddr
            yield AddressInfo(family, host, extra)


class PythonResolver(BaseResolver):
    """DNS resolver that uses a Python implementation.

    This class will use a Python implementation of resolving DNS names.
    It does not use the OS' DNS resolver.
    """
    PREFERENCE_RECORD_MAP = {
        IPFamilyPreference.any: ('A', 'AAAA'),
        IPFamilyPreference.ipv4_only: ('A', ),
        IPFamilyPreference.ipv6_only: ('AAAA', )
    }

    def __init__(self, *args, nameservers: Optional[List[str]]=None, **kwargs):
        """
        Args:
            nameservers: A list of hostnames of DNS servers.
        """
        super().__init__(*args, **kwargs)

        if nameservers:
            self._dns_resolver = dns.resolver.Resolver(configure=False)
            self._dns_resolver.nameservers = nameservers
        else:
            self._dns_resolver = dns.resolver.Resolver()

    async def resolve(self, host: str, timeout: Optional[float]=None) \
            -> ResolverResult:
        record_types = self.PREFERENCE_RECORD_MAP[self._family_preference]

        event_loop = asyncio.get_event_loop()

        address_infos = []
        dns_infos = []

        if timeout:
            self._dns_resolver.lifetime = timeout

        for record_type in record_types:
            query = functools.partial(
                self._dns_resolver.query, host, record_type,
                source=self._bind_address)

            try:
                with self._reraise_dns_error():
                    fetch_date = datetime.datetime.utcnow()
                    answer = await asyncio.wait_for(
                        event_loop.run_in_executor(None, query),
                        timeout=timeout
                    )
            except asyncio.TimeoutError as error:
                raise NetworkTimeoutError('DNS resolve timed out.') from error
            else:
                address_infos.extend(self._convert_dns_answer(answer))
                dns_infos.append(
                    DNSRecordInfo(fetch_date, answer.response.answer)
                )

        return ResolverResult(address_infos, dns_infos)

    @classmethod
    @contextlib.contextmanager
    def _reraise_dns_error(cls):
        try:
            yield
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as error:
            # dnspython doesn't raise an instance with a message, so use the
            # class name instead.
            raise DNSNotFound(
                'DNS resolution failed: {error}'
                .format(error=wbull.util.get_exception_message(error))
            ) from error
        except dns.resolver.Timeout as error:
            raise NetworkTimeoutError('DNS resolve timed out.') from error
        except dns.exception.DNSException as error:
            raise ConnectionError(
                'DNS resolution error: {error}'
                .format(error=wbull.util.get_exception_message(error))
            ) from error

    @classmethod
    def _convert_dns_answer(cls, answer: dns.resolver.Answer) -> Iterable[AddressInfo]:
        assert answer.rdtype in (dns.rdatatype.A, dns.rdatatype.AAAA)

        if answer.rdtype == dns.rdatatype.A:
            family = socket.AF_INET
        else:
            family = socket.AF_INET6

        for record in answer:
            ip_address = record.to_text()

            yield AddressInfo(family, ip_address, ())


class Resolver(BaseResolver):
    """General purpose DNS resolver.

    This class will use a Python implementation to fetch DNS records
    directly and fallback to using the OS' DNS resolver.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._os_resolver = OSResolver(*args, **kwargs)
        self._python_resolver = PythonResolver(*args, **kwargs)

    async def resolve(self, host: str, timeout: Optional[float]=None) \
            -> ResolverResult:
        try:
            return await self._python_resolver.resolve(host, timeout=timeout)
        except DNSNotFound:
            return await self._os_resolver.resolve(host, timeout=timeout)
