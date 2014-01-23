from itertools import cycle
import logging

from kafka.common import ProduceRequest
from kafka.protocol import create_message
from kafka.partitioner import HashedPartitioner

log = logging.getLogger("kafka")


class Producer(object):

    """
    Base class to be used by producers

    Params:
    client - The Kafka client instance to use
    topic - The topic for sending messages to
    req_acks - A value indicating the acknowledgements that the server must
               receive before responding to the request
    ack_timeout - Value (in milliseconds) indicating a timeout for waiting
                  for an acknowledgement
    """

    ACK_AFTER_LOCAL_WRITE = 1       # Send response after it is written to log
    DEFAULT_ACK_TIMEOUT = 1000

    def __init__(self, client, async=False,
                 req_acks=ACK_AFTER_LOCAL_WRITE,
                 ack_timeout=DEFAULT_ACK_TIMEOUT):
        self.client = client
        self.req_acks = req_acks
        self.ack_timeout = ack_timeout

    def send_messages(self, partition, *msg):
        """
        Helper method to send produce requests
        """
        messages = [create_message(m) for m in msg]
        req = ProduceRequest(self.topic, partition, messages)
        try:
            resp = self.client.send_produce_request(
                [req],
                acks=self.req_acks,
                timeout=self.ack_timeout
            )
        except Exception as e:
            log.exception("Unable to send messages")
            raise e
        return resp


class SimpleProducer(Producer):

    """
    A simple, round-robbin producer. Each message goes to exactly one partition

    Params:
    client - The Kafka client instance to use
    topic - The topic for sending messages to
    req_acks - A value indicating the acknowledgements that the server must
               receive before responding to the request
    ack_timeout - Value (in milliseconds) indicating a timeout for waiting
                  for an acknowledgement
    """

    def __init__(self, client, topic,
                 req_acks=Producer.ACK_AFTER_LOCAL_WRITE,
                 ack_timeout=Producer.DEFAULT_ACK_TIMEOUT):
        self.topic = topic
        client._load_metadata_for_topics(topic)
        self.next_partition = cycle(client.topic_partitions[topic])

        super(SimpleProducer, self).__init__(client, req_acks, ack_timeout)

    def send_messages(self, *msg):
        partition = self.next_partition.next()
        return super(SimpleProducer, self).send_messages(partition, *msg)


class KeyedProducer(Producer):

    """
    A producer which distributes messages to partitions based on the key

    Args:
    client - The kafka client instance
    topic - The kafka topic to send messages to
    partitioner - A partitioner class that will be used to get the partition
        to send the message to. Must be derived from Partitioner
    ack_timeout - Value (in milliseconds) indicating a timeout for waiting
                  for an acknowledgement
    """

    def __init__(self, client, topic, partitioner=None,
                 req_acks=Producer.ACK_AFTER_LOCAL_WRITE,
                 ack_timeout=Producer.DEFAULT_ACK_TIMEOUT):
        self.topic = topic
        client._load_metadata_for_topics(topic)

        if not partitioner:
            partitioner = HashedPartitioner

        self.partitioner = partitioner(client.topic_partitions[topic])

        super(KeyedProducer, self).__init__(client, req_acks, ack_timeout)

    def send_message(self, key, msg):
        partitions = self.client.topic_partitions[self.topic]
        partition = self.partitioner.partition(key, partitions)
        return Producer.send_messages(self, partition, msg)
