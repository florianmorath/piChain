#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
   name='pichain',
   packages=find_packages(),
   entry_points='''
       [console_scripts]
       pichain=piChain.main:main
   '''
)
