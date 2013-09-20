# vim: set et sw=4 sts=4 fileencoding=utf-8:

# Copyright 2013 Dave Hughes.
#
# This file is part of picroscopy.
#
# picroscopy is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# picroscopy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# picroscopy.  If not, see <http://www.gnu.org/licenses/>.

"A web application using a RaspberryPi and Picam for microscopy."

import sys

__version__      = '0.1'
__author__       = 'Dave Hughes'
__author_email__ = 'dave@waveform.org.uk'
__url__          = 'https://www.waveform.org.uk/picroscopy/'
__platforms__    = ['ALL']

__classifiers__ = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: Python :: 3',
    'Topic :: Multimedia :: Graphics :: Capture',
    'Topic :: Scientific/Engineering',
    ]

__keywords__ = [
    'science',
    'microscope',
    'raspberrypi',
    ]

__requires__ = [
    'webob<2.0dev',
    'chameleon<3.0dev',
    'wheezy.routing<2.0dev',
    'pillow<3.0dev',
    ]

__extra_requires__ = {
    'doc': ['sphinx'],
    }

if sys.version_info < (3, 3):
    __requires__.extend([
        # Use the IPy library on Python 3.2; 3.3+ uses the built-in ipaddress
        # module
        'IPy<2.0dev',
        ])
    __extra_requires__['doc'].extend([
        # Versions are required for Python 3.2 compatibility. The ordering is
        # reversed because that's what easy_install needs...
        'Jinja2<2.7',
        'MarkupSafe<0.16',
        ])

__entry_points__ = {
    'console_scripts': [
        'picroscopy = picroscopy.terminal:main',
        ],
    }

