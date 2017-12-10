#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

version = '1.0'


def get_long_desc():
    with open('README.md') as f:
        return f.read()


install_requires = [
    'scipy',
]

test_requires = [
    'pytest',
]

setup(
    name='pyelan',
    version=version,
    description="Python library for ELAN",
    long_description="Python library for ELAN",
    url='https://github.com/jonkeane/pyelan/',

    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    author='Jonathan Keane',
    author_email='jkeane@gmail.com',
    license='GPL3 License',
    install_requires=install_requires,
    tests_require=test_requires,
    extras_require={
        'testing': test_requires,
    },
    packages=find_packages(exclude=['tests']),
    # package_dir={'': 'pyelan'},
    include_package_data=True,
    entry_points={},
    py_modules=[splitext(basename(path))[0] for path in glob('pyelan/*.py')],
    # namespace_packages=['pyelan'],
    zip_safe=True,
)