class UnknownException(Exception):
    pass


class OffsetOutOfRange(Exception):
    pass


class InvalidMessage(Exception):
    pass


class UnknownTopicOrPartition(Exception):
    pass


class InvalidMessageSize(Exception):
    pass


class LeaderNotAvailable(Exception):
    pass


class NotLeaderForPartition(Exception):
    pass


class RequestTimedOut(Exception):
    pass


class BrokerNotAvailable(Exception):
    pass


class ReplicaNotAvailable(Exception):
    pass


class MessageSizeTooLarge(Exception):
    pass


class StaleControllerEpochCode(Exception):
    pass


class OffsetMetadataTooLargeCode(Exception):
    pass
