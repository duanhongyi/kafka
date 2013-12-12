
from setuptools import setup

setup(
    name="kafka",
    install_requires=["distribute", "poolbase"],
    packages=["kafka"],
    author="duanhongyi",
    author_email="duanhongyi@doopai.com",
    url="https://github.com/duanhongyi/kafka",
    license="Copyright 2012, David Arthur under Apache License, v2.0",
    description="Pure Python client for Apache Kafka",
    long_description="""
        This module provides low-level protocol support for Apache Kafka as well as
        high-level consumer and producer classes. Request batching is supported by the
        protocol as well as broker-aware request routing. Gzip and Snappy compression
        is also supported for message sets.
    """
)
