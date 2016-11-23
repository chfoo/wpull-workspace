import socket
import unittest

from wbull.exceptions import DNSNotFound, NetworkTimeoutError
from wbull.network.dns import OSResolver, PythonResolver, Resolver, BaseResolver, \
    IPFamilyPreference, ResolverResult, AddressInfo
from wbull.testing.async import AsyncTestCase, async_test


class DNSTestMixin:
    def get_resolver(self, *args, **kwargs) -> BaseResolver:
        return BaseResolver(*args, **kwargs)

    @async_test()
    async def test_live_google(self):
        resolver = self.get_resolver()
        result = await resolver.resolve('google.com')

        address4 = result.first_ipv4
        address6 = result.first_ipv6

        self.assertEqual(socket.AF_INET, address4.family)
        self.assertIsInstance(address4.ip_address, str)
        self.assertIn('.', address4.ip_address)

        self.assertEqual(socket.AF_INET6, address6.family)
        self.assertIsInstance(address6.ip_address, str)
        self.assertIn(':', address6.ip_address)

        result.shuffle()
        result.rotate()

    @async_test()
    async def test_invalid_domain(self):
        resolver = self.get_resolver()

        with self.assertRaises(DNSNotFound):
            await resolver.resolve('test.invalid')

    @async_test()
    async def test_invalid_domain_ipv6(self):
        resolver = self.get_resolver(family_preference=IPFamilyPreference.ipv6_only)

        with self.assertRaises(DNSNotFound):
            await resolver.resolve('test.invalid')


class TestOSDNSResolver(AsyncTestCase, DNSTestMixin):
    def get_resolver(self, *args, **kwargs):
        return OSResolver(*args, **kwargs)

    @async_test()
    async def test_localhost(self):
        resolver = self.get_resolver(family_preference=IPFamilyPreference.ipv4_only)
        result = await resolver.resolve('localhost')

        address4 = result.first_ipv4
        address6 = result.first_ipv6

        self.assertEqual(socket.AF_INET, address4.family)
        self.assertIsInstance(address4.ip_address, str)
        self.assertIn('.', address4.ip_address)

        self.assertFalse(address6)


class TestPythonDNSResolver(AsyncTestCase, DNSTestMixin):
    def get_resolver(self, *args, **kwargs):
        return PythonResolver(*args, **kwargs)

    @async_test()
    async def test_leading_hyphen_domain(self):
        resolver = self.get_resolver()

        await resolver.resolve('-test.fart.website')

    @async_test()
    async def test_timeout(self):
        resolver = self.get_resolver(nameservers=['10.0.0.0'])

        with self.assertRaises(NetworkTimeoutError):
            await resolver.resolve('test.invalid', timeout=0.1)

    @async_test()
    async def test_resource_record(self):
        resolver = self.get_resolver()
        result = await resolver.resolve('google.com')

        dns_info = result.dns_records[0]
        text = dns_info.to_text_format()
        lines = text.splitlines()

        self.assertRegex(lines[0], r'\d{14}', 'date string')
        self.assertEqual(5, len(lines[1].split()), 'resource record')


class TestDNSResolver(AsyncTestCase, DNSTestMixin):
    def get_resolver(self, *args, **kwargs):
        return Resolver(*args, **kwargs)


class DNSTestCase(unittest.TestCase):
    def test_resolver_result(self):
        resolver_result = ResolverResult([
            AddressInfo(socket.AF_INET6, '[::1]', None),
            AddressInfo(socket.AF_INET6, '[::2]', None),
            AddressInfo(socket.AF_INET, '127.0.0.1', None),
            AddressInfo(socket.AF_INET, '127.0.0.2', None),
        ])

        self.assertEqual(4, len(resolver_result.addresses))
        self.assertEqual('[::1]', resolver_result.first.ip_address)
        self.assertEqual('[::1]', resolver_result.first_ipv6.ip_address)
        self.assertEqual('127.0.0.1', resolver_result.first_ipv4.ip_address)

        resolver_result.rotate()
        self.assertEqual(4, len(resolver_result.addresses))
        self.assertEqual('[::2]', resolver_result.first.ip_address)

        resolver_result.shuffle()
        self.assertEqual(4, len(resolver_result.addresses))
