##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup

$Id: setup.py 101333 2009-06-30 03:03:10Z srichter $
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup (
    name='topia.termextract',
    version='1.1.0',
    author = "Stephan Richter, Russ Ferriday and the Zope Community",
    author_email = "zope3-dev@zope.org",
    description = "Content Term Extraction using POS Tagging",
    long_description=(
        read('README.txt')
        + '\n\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'topia', 'termextract', 'README.txt')
        + '\n\n' +
        read('src', 'topia', 'termextract', 'example.txt')
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license = "ZPL 2.1",
    keywords = "content term extract pos tagger linguistics",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    url = 'http://pypi.python.org/pypi/topia.termextract',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['topia'],
    extras_require = dict(
        test = ['zope.testing'],
        ),
    install_requires = [
        'setuptools',
        'zope.interface',
        ],
    zip_safe = False,
    )
