#!/usr/bin/env python3
# vim: set et sw=4 sts=4:

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from utils import description, get_version

if not sys.version_info >= (3, 2):
    raise ValueError('This package requires Python 3.2 or above')

HERE = os.path.abspath(os.path.dirname(__file__))

# All meta-data is defined as global variables so that other modules can query
# it easily without having to wade through distutils nonsense
NAME         = 'picroscopy'
DESCRIPTION  = 'A web application using a RaspberryPi for microscopy'
KEYWORDS     = ['science', 'microscope', 'raspberrypi']
AUTHOR       = 'Dave Hughes'
AUTHOR_EMAIL = 'dave@waveform.org.uk'
MANUFACTURER = 'waveform'
URL          = 'https://www.waveform.org.uk/picroscopy/'

REQUIRES = [
    # For some bizarre reason, matplotlib doesn't "require" numpy in its
    # setup.py. The ordering below is also necessary to ensure numpy gets
    # picked up first ... yes, it's backwards ...
    'webob<=2.0dev',
    'chameleon<=3.0dev',
    'wheezy.routing<=2.0dev',
    'pillow<=3.0dev',
    ]

EXTRA_REQUIRES = {
    }

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: Python :: 3.2',
    'Topic :: Multimedia :: Graphics',
    'Topic :: Scientific/Engineering',
    ]

ENTRY_POINTS = {
    'console_scripts': [
        'picroscopy = picroscopy.terminal:main',
        ],
    }

PACKAGES = [
    'picroscopy',
    ]

PACKAGE_DATA = {
    }


# Add a py.test based "test" command
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--cov', NAME,
            '--cov-report', 'term-missing',
            '--cov-report', 'html',
            '--cov-config', 'coverage.cfg',
            'tests',
            ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def main():
    setup(
        name                 = NAME,
        version              = get_version(os.path.join(HERE, NAME, '__init__.py')),
        description          = DESCRIPTION,
        long_description     = description(os.path.join(HERE, 'README.rst')),
        classifiers          = CLASSIFIERS,
        author               = AUTHOR,
        author_email         = AUTHOR_EMAIL,
        url                  = URL,
        keywords             = ' '.join(KEYWORDS),
        packages             = PACKAGES,
        package_data         = PACKAGE_DATA,
        include_package_data = True,
        platforms            = 'ALL',
        install_requires     = REQUIRES,
        extras_require       = EXTRA_REQUIRES,
        zip_safe             = True,
        entry_points         = ENTRY_POINTS,
        tests_require        = ['pytest-cov', 'pytest', 'mock'],
        cmdclass             = {'test': PyTest},
        )

if __name__ == '__main__':
    main()

