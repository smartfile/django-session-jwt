#!/bin/env python

import os
from os.path import join as pathjoin
from os.path import dirname
from subprocess import check_output, CalledProcessError
from setuptools import setup
from setuptools import find_packages


package_name = 'django-session-jwt'
readme = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(readme) as readme_file:
    long_description = readme_file.read()
version_msg = '# Do not edit. See setup.py.{nl}__version__ = "{ver}"{nl}'
version_py = pathjoin(
    dirname(__file__), package_name.replace('-', '_'), 'version.py')

# Get version from GIT or version.py.
try:
    version_git = check_output(['git', 'describe', '--tags']).rstrip()
    version_git = version_git.decode('utf-8')
except (CalledProcessError, OSError):
    with open(version_py, 'rt') as f:
        version_git = f.read().strip().split('=')[-1].replace('"', '')
else:
    # Write out version.py.
    with open(version_py, 'wt') as f:
        f.write(version_msg.format(ver=version_git, nl=os.linesep))


setup(
    name = package_name,
    version = version_git,
    description = 'A django application that combines django.contrib.sessions with JWT.',
    long_description = long_description,
    author = 'SmartFile',
    author_email = 'team@smartfile.com',
    maintainer = 'Ben Timby',
    maintainer_email = 'btimby@smartfile.com',
    url = 'http://github.com/smartfile/' + package_name + '/',
    license = 'MIT',
    install_requires = [
        'pyjwt>=2',
    ],
    packages = find_packages(),
    classifiers = (
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
