class FailedPayloadsException(Exception):
    pass


class ConnectionError(Exception):
    pass


class BufferUnderflowError(Exception):
    pass


class ChecksumError(Exception):
    pass


class ConsumerFetchSizeTooSmall(Exception):
    pass


class ConsumerNoMoreData(Exception):
    pass
