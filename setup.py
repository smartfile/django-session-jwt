#!/bin/env python

import os
from setuptools import setup

name = 'django-session-jwt'
version = '0.1'
readme = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(readme) as readme_file:
    long_description = readme_file.read()

setup(
    name = name,
    version = version,
    description = 'A django application that combines django.contrib.sessions with JWT.',
    long_description = long_description,
    author = 'SmartFile',
    author_email = 'team@smartfile.com',
    maintainer = 'Ben Timby',
    maintainer_email = 'btimby@smartfile.com',
    url = 'http://github.com/smartfile/' + name + '/',
    license = 'MIT',
    install_requires = [
    ],
    packages = [
        "django_session_jwt",
    ],
    classifiers = (
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
