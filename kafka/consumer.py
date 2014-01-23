from itertools import izip_longest, repeat
import logging

from kafka.common import (
    FetchRequest,
    OffsetRequest, OffsetCommitRequest,
    ConsumerFetchSizeTooSmall, ConsumerNoMoreData,
    OffsetFetchRequest
)


log = logging.getLogger("kafka")


FETCH_MAX_WAIT_TIME = 100
FETCH_MIN_BYTES = 4096


class Consumer(object):

    """
    Base class to be used by other consumers. Not to be used directly

    This base class provides logic for
    * initialization and fetching metadata of partitions
    * APIs for fetching pending message count
    """

    def __init__(self, client, group, topic, partitions=None):

        self.client = client
        self.current_buffer_size = client.buffer_size
        self.topic = topic
        self.group = group
        self.client._load_metadata_for_topics(topic)
        self.offsets = {}

        if not partitions:
            partitions = self.client.topic_partitions[topic]

        for partition in partitions:
            req = OffsetFetchRequest(topic, partition)
            (offset,) = self.client.send_offset_fetch_request(
                group,
                [req],
                fail_on_error=False
            )
            self.offsets[partition] = offset.offset

    def commit(self, partitions=None):
        """
        Commit offsets for this consumer

        partitions: list of partitions to commit, default is to commit
                    all of them
        """

        # short circuit if nothing happened. This check is kept outside
        # to prevent un-necessarily acquiring a lock for checking the state
        reqs = []
        if not partitions:  # commit all partitions
            partitions = self.offsets.keys()

        for partition in partitions:
            offset = self.offsets[partition]
            log.debug("Commit offset %d in SimpleConsumer: "
                      "group=%s, topic=%s, partition=%s" %
                      (offset, self.group, self.topic, partition))

            reqs.append(OffsetCommitRequest(self.topic, partition,
                                            offset, None))
        resps = self.client.send_offset_commit_request(self.group, reqs)
        for resp in resps:
            assert resp.error == 0

    def pending(self, partitions=None):
        """
        Gets the pending message count

        partitions: list of partitions to check for, default is to check all
        """
        if not partitions:
            partitions = self.offsets.keys()

        total = 0
        reqs = []

        for partition in partitions:
            reqs.append(OffsetRequest(self.topic, partition, -1, 1))

        resps = self.client.send_offset_request(reqs)
        for resp in resps:
            partition = resp.partition
            pending = resp.offsets[0]
            offset = self.offsets[partition]
            total += pending - offset - (1 if offset > 0 else 0)

        return total


class SimpleConsumer(Consumer):

    """
     consumer implementation that consumes all/specified partitions
    for a topic

    client: a connected KafkaClient
    group: a name for this consumer, used for offset storage and must be unique
    topic: the topic to consume
    partitions: An optional list of partitions to consume the data from
    """

    def __init__(self, client, group, topic, partitions=None,
                 fetch_max_wait_time=FETCH_MAX_WAIT_TIME,
                 fetch_size_bytes=FETCH_MIN_BYTES):

        self.partition_info = False     # Do not return partition info in msgs
        self.fetch_max_wait_time = fetch_max_wait_time
        self.fetch_min_bytes = fetch_size_bytes

        super(SimpleConsumer, self).__init__(
            client, group, topic,
            partitions=partitions)

    def provide_partition_info(self):
        """
        Indicates that partition info must be returned by the consumer
        """
        self.partition_info = True

    def seek(self, offset, whence):
        """
        Alter the current offset in the consumer, similar to fseek

        offset: how much to modify the offset
        whence: where to modify it from
                0 is relative to the earliest available offset (head)
                1 is relative to the current offset
                2 is relative to the latest known offset (tail)
        """

        if whence == 1:  # relative to current position
            for partition, _offset in self.offsets.items():
                self.offsets[partition] = _offset + offset
        elif whence in (0, 2):  # relative to beginning or end
            # divide the request offset by number of partitions,
            # distribute the remained evenly
            (delta, rem) = divmod(offset, len(self.offsets))
            deltas = {}
            for partition, r in izip_longest(self.offsets.keys(),
                                             repeat(1, rem), fillvalue=0):
                deltas[partition] = delta + r

            reqs = []
            for partition in self.offsets.keys():
                if whence == 0:
                    reqs.append(OffsetRequest(self.topic, partition, -2, 1))
                elif whence == 2:
                    reqs.append(OffsetRequest(self.topic, partition, -1, 1))

                    # The API returns back the next available offset
                    # For eg: if the current offset is 18, the API will return
                    # back 19. So, if we have to seek 5 points before, we will
                    # end up going back to 14, instead of 13. Adjust this
                    deltas[partition] -= 1
                else:
                    pass

            resps = self.client.send_offset_request(reqs)
            for resp in resps:
                self.offsets[resp.partition] = \
                    resp.offsets[0] + deltas[resp.partition]
        else:
            raise ValueError("Unexpected value for `whence`, %d" % whence)

    def get_messages(self, count=1):
        """
        Fetch the specified number of messages and commit offset

        count: Indicates the maximum number of messages to be fetched
        block: If True, the API will block till some messages are fetched.
        """
        messages = []
        iterator = self.__iter__()

        while count > 0:
            try:
                messages.append(next(iterator))
            except StopIteration:
                break
            count -= 1
        self.commit()
        return messages

    def __iter__(self):
        """
        Create an iterate per partition. Iterate through them calling next()
        until they are all exhausted.
        """
        iters = {}
        for partition, offset in self.offsets.items():
            iters[partition] = self.__iter_partition__(partition, offset)

        if len(iters) == 0:
            return

        while True:
            if len(iters) == 0:
                break

            for partition, it in iters.items():
                try:
                    if self.partition_info:
                        yield (partition, it.next())
                    else:
                        yield it.next()
                except StopIteration:
                    log.debug("Done iterating over partition %s" % partition)
                    del iters[partition]

    def __iter_partition__(self, partition, offset):
        """
        Iterate over the messages in a partition. Create a FetchRequest
        to get back a batch of messages, yield them one at a time.
        After a batch is exhausted, start a new batch unless we've reached
        the end of this partition.
        """

        # The offset that is stored in the consumer is the offset that
        # we have consumed. In subsequent iterations, we are supposed to
        # fetch the next message (that is from the next offset)
        # However, for the 0th message, the offset should be as-is.
        # An OffsetFetchRequest to Kafka gives 0 for a new queue. This is
        # problematic, since 0 is offset of a message which we have not yet
        # consumed.
        offset = offset + 1
        fetch_size = self.fetch_min_bytes
        while True:
            req = FetchRequest(
                self.topic, partition, offset, self.current_buffer_size)
            (resp,) = self.client.send_fetch_request(
                [req],
                max_wait_time=self.fetch_max_wait_time,
                min_bytes=fetch_size)
            assert resp.topic == self.topic
            assert resp.partition == partition
            try:
                for message in resp.messages:
                    self.current_buffer_size = self.client.buffer_size
                    self.offsets[partition] = message.offset
                    yield message
                    if message.offset is None:
                        break
                    offset = message.offset + 1
            except ConsumerFetchSizeTooSmall as e:
                self.current_buffer_size *= 2
                log.warn(
                    "Fetch size too small, increasing to %d (2x) and retry",
                    self.current_buffer_size)
                continue
            except ConsumerNoMoreData as e:
                log.debug("Iteration was ended by %r", e)
