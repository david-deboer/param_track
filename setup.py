#! /usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# Copyright 2022 David DeBoer
# Licensed under the 2-clause BSD license.

from setuptools import setup
import glob

setup_args = {
    'name': "param_track",
    'description': "parameter tracking",
    'license': "BSD",
    'author': "David DeBoer",
    'author_email': "david.r.deboer@gmail.com",
    'version': '0.8',
    'packages': ['param_track']
    #'install_requires': ['pyyaml', 'json']
}

if __name__ == '__main__':
    setup(**setup_args)
