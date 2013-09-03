"""A web application using a RaspberryPi and Picam for microscopy."""

__version__      = '0.1'
__author__       = 'Dave Hughes'
__author_email__ = 'dave@waveform.org.uk'
__url__          = 'https://www.waveform.org.uk/picroscopy/'
__platforms__    = 'ALL'

__requires__ = [
    'webob<=2.0dev',
    'chameleon<=3.0dev',
    'wheezy.routing<=2.0dev',
    'pillow<=3.0dev',
    ]

__extra_requires__ = {
    }

__classifiers__ = [
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

__keywords__ = [
    'science',
    'microscope',
    'raspberrypi',
    ]

__entry_points__ = {
    'console_scripts': [
        'picroscopy = picroscopy.terminal:main',
        ],
    }

