import asyncio
import logging
import ssl

import wbull.cert

_logger = logging.getLogger(__name__)


class EchoServer:
    async def __call__(self, reader, writer):
        _logger.debug('Connected')

        while True:
            _logger.debug('Waiting for line')
            data = await reader.readline()

            _logger.debug('Got %s', data)

            if not data:
                writer.close()
                break

            writer.write(data)

        _logger.debug('Disconnected')


class EchoServerTestMixin:
    def _get_server_ssl(self):
        return None

    def setUp(self):
        super().setUp()
        self._server = EchoServer()
        coro = asyncio.start_server(self._server, host='localhost',
                                    ssl=self._get_server_ssl())
        self._server_handle = asyncio.get_event_loop().run_until_complete(coro)
        self.address = self._server_handle.sockets[0].getsockname()

    def tearDown(self):
        super().tearDown()
        self._server_handle.close()


class SSLEchoServerTestMixin(EchoServerTestMixin):
    def _get_server_ssl(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        wbull.cert.load_self_signed_cert(context)

        return context
