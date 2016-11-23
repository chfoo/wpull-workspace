"""Asynchronous Network Connections

This module provides a convenient wrapper to low level operations on
asyncio streams for TCP sockets.
"""

import asyncio
import ssl

from typing import Union, Optional, Iterable


class Connection:
    """A wrapper for asyncio StreamReader and Streamwriter.

    Args:
        reader: A connected stream reader.
        writer: A connected stream writer.
    """
    def __init__(self, reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        super().__init__()
        self._reader = reader
        self._writer = writer

    @classmethod
    async def connect(cls, address: tuple, bind_host: Optional[str]=None) \
            -> 'Connection':
        """Open a new connection.

        Args:
            address: A hostname and port number.
            bind_host: A hostname to bind the socket on the local
                machine. This is used for cases when the machine
                as multiple IP addresses.
        """
        assert len(address) >= 2, \
            'Expected host & port, got {}'.format(address)
        assert isinstance(address[0], str), \
            'Expect str, got {}'.format(type(address[0]))
        assert isinstance(address[1], int), \
            'Expect int, got {}'.format(type(address[1]))

        # TODO: pass flow-info and scope-id

        local_addr = None

        if bind_host:
            local_addr = (bind_host, 0)

        reader, writer = await asyncio.open_connection(
            host=address[0], port=address[1], local_addr=local_addr)

        return Connection(reader, writer)

    def close(self):
        """Disconnect the stream."""
        self._writer.close()

    async def write(self, data: bytes, drain: bool=True):
        """Send data through the stream writer.

        Args:
            data: The data to be sent.
            drain: Whether to wait for data to be sent before continuing.

        :see_also: :meth:`asyncio.StreamWriter.write`
        """
        self._writer.write(data)

        if drain:
            await self._writer.drain()

    async def writelines(self, lines: Iterable[bytes], drain: bool=True):
        """Send data through the stream writer.

        Args:
            lines: Lines of data to be sent.
            drain: Whether to wait for data to be sent before continuing.

        :see_also: :meth:`asyncio.StreamWriter.writelines`
        """
        self._writer.writelines(lines)

        if drain:
            await self._writer.drain()

    async def read(self, amount: int=-1, exact: bool=False) -> bytes:
        """Receive data through the stream reader.

        Args:
            amount: Number of bytes to read. Specify -1 to read
                until the stream is closed.
            exact: If `True` and `amount `is given, the stream will be
                read exactly given amount of bytes.

        :see_also: :meth:`asyncio.StreamReader.read`
        """
        if exact:
            return await self._reader.readexactly(amount)
        else:
            return await self._reader.read(amount)

    async def readline(self) -> bytes:
        """Receive a line of data from the stream reader.

        :see_also: :meth:`asyncio.StreamReader.readline`
        """
        return await self._reader.readline()

    async def start_tls(self, ssl_context: Union[bool, ssl.SSLContext]=True,
                        server_hostname: Optional[str]=None):
        """Negotiate a TLS connection.

        Args:
            ssl_context: A SSL context to configure the TLS settings.
                By default, an insecure configuration is used. Use
                :func:`ssl.create_ssl_context` instead.
            server_hostname: A hostname to used to verify SSL
                certificates. If none is provided, the hostname
                is determined from the underlying socket.

        This method can be called at anytime and multiple times.
        """

        sock = self._writer.get_extra_info('socket')

        if not server_hostname:
            server_hostname = sock.getsockname()[0]

        self._reader, self._writer = await asyncio.open_connection(
            sock=sock, ssl=ssl_context, server_hostname=server_hostname)
