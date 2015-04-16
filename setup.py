from os import listdir
from os.path import join, sep

from setuptools import setup


setup(
    name='netdev',
    version='0.0.1',
    description='Device manager for network devices',
    author='Brett Ponsler',
    author_email='ponsler@gmail.com',
    url='',
    packages=['netdev'],
    test_suite="netdev.tests",
    )
