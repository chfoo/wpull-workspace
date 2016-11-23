import ssl

from wbull.network.connection import Connection
from wbull.testing.async import AsyncTestCase, async_test
from wbull.testing.server import EchoServerTestMixin, SSLEchoServerTestMixin


class TestConnection(EchoServerTestMixin, AsyncTestCase):
    async def get_connection(self, **kwargs) -> Connection:
        return await Connection.connect(self.address, **kwargs)

    @async_test()
    async def test_connection_read_write(self):
        connection = await self.get_connection()

        # Test lots of write/reads
        for dummy in range(100):
            await connection.write(b'hello world\n')
            response = await connection.readline()

            self.assertEqual(b'hello world\n', response)

        # Test basic read
        await connection.write(b'hello world\n')
        response = await connection.read(len(b'hello world\n'))
        self.assertEqual(b'hello world\n', response)

        # Test readexact
        await connection.write(b'hello world\n')
        response = await connection.read(len(b'hello world\n'), exact=True)
        self.assertEqual(b'hello world\n', response)

        # Test writelines
        await connection.writelines([b'hello world\n'])
        response = await connection.readline()
        self.assertEqual(b'hello world\n', response)

        connection.close()

    @async_test()
    async def test_connection_bind_host(self):
        connection = await self.get_connection(bind_host='127.0.0.1')

        await connection.write(b'hello world\n')
        response = await connection.readline()

        self.assertEqual(b'hello world\n', response)

        connection.close()


class TestSSLConnection(SSLEchoServerTestMixin, TestConnection):
    async def get_connection(self, **kwargs):
        connection = await super().get_connection(**kwargs)
        await connection.start_tls(ssl_context=ssl.SSLContext(ssl.PROTOCOL_SSLv23))
        return connection
