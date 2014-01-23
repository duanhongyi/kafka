class UnknownException(Exception):
    pass


class OffsetOutOfRangeException(Exception):
    pass


class InvalidMessageException(Exception):
    pass


class UnknownTopicOrPartitionException(Exception):
    pass


class InvalidMessageSizeException(Exception):
    pass


class LeaderNotAvailableException(Exception):
    pass


class NotLeaderForPartitionException(Exception):
    pass


class RequestTimedOutException(Exception):
    pass


class BrokerNotAvailableException(Exception):
    pass


class ReplicaNotAvailableException(Exception):
    pass


class MessageSizeTooLargeException(Exception):
    pass


class StaleControllerEpochCodeException(Exception):
    pass


class OffsetMetadataTooLargeCodeException(Exception):
    pass
