# Kafka Python client

This module provides low-level protocol support for Apache Kafka as well as
high-level consumer and producer classes. Request batching is supported by the
protocol as well as broker-aware request routing. Gzip and Snappy compression
is also supported for message sets.

Compatible with Apache Kafka 0.8.1

http://kafka.apache.org/

# About

This client is based on python-kafka, python-kafka was created by David Arthur.
However, because its implementation is more complex, in practical applications
can not be good support gevent, so I had to rewrite using connection pooling, and
delete some of the features.


# License

This pack is Copyright 2013, Apache License, v2.0. See `LICENSE`


## High level

```python
from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer, KeyedProducer

kafka = KafkaClient("localhost", 9092, pool_size=20, auto_connect=True)

# To send messages synchronously
producer = SimpleProducer(kafka, "my-topic")
producer.send_messages("some message")
producer.send_messages("this method", "is variadic")


# To consume messages
consumer = SimpleConsumer(kafka, "my-group", "my-topic")

# iter get need commit
while True:
    for partition, message in consumer:
        print("partition:%s,message:%s" % (partition, message))
    consumer.commit()

# Do not need commit
for partition, message in consumer.get_messages(count=5):
    print("partition:%s,message:%s" % (partition, message))

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

# Install

Install with your favorite package manager

Pip:

```shell
pip install kafka
```

Setuptools:
```shell
easy_install kafka
```

Using `setup.py` directly:
```shell
git clone https://github.com/duanhongyi/kafka
cd kafka
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
