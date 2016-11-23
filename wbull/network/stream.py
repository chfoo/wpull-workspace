"""Data Streams

Streams provide an abstraction for data transfer on underlying
connections. This abstraction allows swapping connections on-the-fly
to support operations such as tunneling or proxies.
"""
from typing import Optional

import asyncio

from wbull.exceptions import NetworkTimeoutError
from wbull.network.connection import Connection


class Stream:
    def __init__(self, connection: Connection):
        self._connection = connection
        self._closed = False

    @property
    def connection(self) -> Connection:
        """The underlying connection."""
        return self._connection

    @connection.setter
    def connection(self, value: Connection):
        self._connection = value

    @classmethod
    async def connect(cls, *args, timeout: Optional[float]=None, **kwargs) \
            -> 'Stream':
        """Open a new connection and return a new stream.

        Args:
            timeout: Time in seconds before `NetworkTimeoutError`
                is raised.

        :see_also: :meth:`.Connection.connect`
        """
        connection = await _run_network_operation(
            Connection.connect(*args, **kwargs), timeout, 'Connect'
        )
        return Stream(connection)

    def close(self):
        """Close the connection."""
        self._connection.close()
        self._closed = True

    @property
    def closed(self) -> bool:
        """Return whether the underlying connection is closed."""
        return self._closed

    async def write(self, *args, timeout: Optional[float]=None, **kwargs):
        """Write data to the connection.

        Args:
            timeout: Time in seconds before `NetworkTimeoutError`
                is raised.

        :see_also: :meth:`.Connection.write`
        """
        await _run_network_operation(
            self._connection.write(*args, **kwargs),
            timeout, 'Write', stream=self
        )

    async def writelines(self, *args, timeout: Optional[float]=None, **kwargs):
        """Write data to the connection.

        Args:
            timeout: Time in seconds before `NetworkTimeoutError`
                is raised.

        :see_also: :meth:`.Connection.writelines`
        """
        await _run_network_operation(
            self._connection.writelines(*args, **kwargs),
            timeout, 'Writelines', stream=self
        )

    async def read(self, *args, timeout: Optional[float]=None, **kwargs) -> bytes:
        """Read data from the connection.

        Args:
            timeout: Time in seconds before `NetworkTimeoutError`
                is raised.

        :see_also: :meth:`.Connection.read`
        """
        return await _run_network_operation(
            self._connection.read(*args, **kwargs),
            timeout, 'Read', stream=self
        )

    async def readline(self, timeout: Optional[float]=None) -> bytes:
        """Read a line from the connection.

        Args:
            timeout: Time in seconds before `NetworkTimeoutError`
                is raised.

        :see_also: :meth:`.Connection.readline`
        """
        return await _run_network_operation(
            self._connection.readline(), timeout, 'Readline', stream=self
        )


async def _run_network_operation(coro, timeout: float, operation_name: str,
                                 stream: Optional[Stream]=None):
    """Runs a network coroutine.

    Args:
        coro: The coroutine.
        timeout: Time in seconds before `NetworkTimeoutError`
            is raised.
        operation_name: Name of operation for exception messages.
        stream: A stream to close if an error occurs.
    """
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError as error:
        if stream:
            stream.close()

        raise NetworkTimeoutError(
            'Network timeout: {}'.format(operation_name)) from error
