import os
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name="kafka",
    version="0.8.1-3",
    install_requires=["distribute", "poolbase"],
    packages=find_packages(),
    author="duanhongyi",
    author_email="duanhongyi@doopai.com",
    url="https://github.com/duanhongyi/kafka",
    license="Copyright 2012, Apache License, v2.0",
    description="Pure Python client for Apache Kafka",
    long_description=README,
)
