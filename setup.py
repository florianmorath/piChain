#!/usr/bin/env python3

from setuptools import find_packages, setup

with open('LICENSE') as f:
    LICENSE = f.read()

setup(
   name='pichain',
   version='0.1dev',
   author='Florian Morath',
   author_email='morathflorian@gmail.com',
   description=('A library which implements a fault-tolerant distributed state machine.'),
   license=LICENSE,
   packages=find_packages(),
)
