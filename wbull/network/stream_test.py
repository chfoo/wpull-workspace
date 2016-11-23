from wbull.exceptions import NetworkTimeoutError
from wbull.network.connection import Connection
from wbull.network.stream import Stream
from wbull.testing.async import AsyncTestCase, async_test
from wbull.testing.server import EchoServerTestMixin


class TestStream(EchoServerTestMixin, AsyncTestCase):
    @async_test()
    async def test_connect_timeout(self):
        with self.assertRaises(NetworkTimeoutError):
            await Stream.connect(('10.0.0.0', 0), timeout=1)

    @async_test()
    async def test_read_timeout(self):
        stream = await Stream.connect(self.address)

        with self.assertRaises(NetworkTimeoutError):
            await stream.read(1, timeout=1)

        self.assertTrue(stream.closed)

    @async_test()
    async def test_echo_and_connection_swap(self):
        connection = await Connection.connect(self.address)
        stream = Stream(connection)

        await stream.writelines([b'hello', b'\n'])
        data = await stream.readline()

        self.assertEqual(b'hello\n', data)

        connection_2 = await Connection.connect(self.address)

        stream.connection = connection_2

        self.assertEqual(connection_2, stream.connection)

        await stream.write(b'hello\n')
        data = await stream.read(6)

        self.assertEqual(b'hello\n', data)
