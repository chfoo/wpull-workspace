class NetworkTimeoutError(ConnectionError):
    pass


class ConnectionClosedError(ConnectionError):
    pass


class DNSNotFound(ConnectionError):
    pass
