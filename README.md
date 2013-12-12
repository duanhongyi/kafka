# Kafka Python client

[![Build Status](https://travis-ci.org/mumrah/kafka-python.png)](https://travis-ci.org/mumrah/kafka-python)

This module provides low-level protocol support for Apache Kafka as well as
high-level consumer and producer classes. Request batching is supported by the
protocol as well as broker-aware request routing. Gzip and Snappy compression
is also supported for message sets.

Compatible with Apache Kafka 0.8.1

http://kafka.apache.org/

# License

Copyright 2013, David Arthur under Apache License, v2.0. See `LICENSE`

# Status

I'm following the version numbers of Kafka, plus one number to indicate the
version of this project. The current version is 0.8.0-1. This version is under
development, APIs are subject to change.

# Usage

## High level

```python
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer, KeyedProducer

kafka = KafkaClient("localhost", 9092)

# To send messages synchronously
producer = SimpleProducer(kafka, "my-topic")
producer.send_messages("some message")
producer.send_messages("this method", "is variadic")

# To send messages asynchronously
producer = SimpleProducer(kafka, "my-topic", async=True)
producer.send_messages("async message")

# To wait for acknowledgements
# ACK_AFTER_LOCAL_WRITE : server will wait till the data is written to
#                         a local log before sending response
# ACK_AFTER_CLUSTER_COMMIT : server will block until the message is committed
#                            by all in sync replicas before sending a response
producer = SimpleProducer(kafka, "my-topic", async=False,
                          req_acks=SimpleProducer.ACK_AFTER_LOCAL_WRITE,
                          acks_timeout=2000)

response = producer.send_messages("async message")

if response:
    print(response[0].error)
    print(response[0].offset)

# To send messages in batch. You can use any of the available
# producers for doing this. The following producer will collect
# messages in batch and send them to Kafka after 20 messages are
# collected or every 60 seconds
# Notes:
# * If the producer dies before the messages are sent, there will be losses
# * Call producer.stop() to send the messages and cleanup
producer = SimpleProducer(kafka, "my-topic", batch_send=True,
                          batch_send_every_n=20,
                          batch_send_every_t=60)

# To consume messages
consumer = SimpleConsumer(kafka, "my-group", "my-topic")

# iter get need commit
for message in consumer:
    print(message)
    consumer.commit()

# Do not need commit
for message in consumer.get_messages(count=5, block=True, timeout=4):
    print(message)

kafka.close()
```

## Keyed messages
```python
from kafka.client import KafkaClient
from kafka.producer import KeyedProducer
from kafka.partitioner import HashedPartitioner, RoundRobinPartitioner

kafka = KafkaClient("localhost", 9092)

# HashedPartitioner is default
producer = KeyedProducer(kafka, "my-topic")
producer.send("key1", "some message")
producer.send("key2", "this methode")

producer = KeyedProducer(kafka, "my-topic", partitioner=RoundRobinPartitioner)
```

## Low level

```python
from kafka.client import KafkaClient
kafka = KafkaClient("localhost", 9092)
req = ProduceRequest(topic="my-topic", partition=1,
    messages=[KafkaProdocol.encode_message("some message")])
resps = kafka.send_produce_request(payloads=[req], fail_on_error=True)
kafka.close()

resps[0].topic      # "my-topic"
resps[0].partition  # 1
resps[0].error      # 0 (hopefully)
resps[0].offset     # offset of the first message sent in this request
```

# Install

Install with your favorite package manager

Pip:

```shell
git clone https://github.com/mumrah/kafka-python
pip install ./kafka-python
```

Setuptools:
```shell
git clone https://github.com/mumrah/kafka-python
easy_install ./kafka-python
```

Using `setup.py` directly:
```shell
git clone https://github.com/mumrah/kafka-python
cd kafka-python
python setup.py install
```

## Optional Snappy install

Download and build Snappy from http://code.google.com/p/snappy/downloads/list

```shell
wget http://snappy.googlecode.com/files/snappy-1.0.5.tar.gz
tar xzvf snappy-1.0.5.tar.gz
cd snappy-1.0.5
./configure
make
sudo make install
```

Install the `python-snappy` module
```shell
pip install python-snappy
```
