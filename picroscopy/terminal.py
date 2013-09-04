#!/usr/bin/env python3

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

"""
This module defines the command line interface for executing the picroscopy
application. The main class, PicroscopyConsoleApp, handles parsing of command
line parameters and configuration files, configuration of the logging system,
and of course launching the application itself within the reference WSGI
server included with Python.
"""

import os
import sys
import logging
import argparse
import subprocess
import locale
import configparser
from wsgiref.simple_server import make_server

from picroscopy import __version__
from picroscopy.wsgi import PicroscopyWsgiApp

# Use the user's default locale instead of C
locale.setlocale(locale.LC_ALL, '')

# Set up a console logging handler which just prints messages without any other
# adornments
_CONSOLE = logging.StreamHandler(sys.stderr)
_CONSOLE.setFormatter(logging.Formatter('%(message)s'))
_CONSOLE.setLevel(logging.DEBUG)
logging.getLogger().addHandler(_CONSOLE)

# Determine the location of the current module on the filesystem
HERE = os.path.abspath(os.path.dirname(__file__))


def size(s):
    """
    Parses a string containing a Width[xHeight] image size specification.
    """
    if 'x' in s:
        w, h = s.split('x', 1)
    else:
        w = h = s
    if not (w.isdigit() and h.isdigit()):
        raise ValueError(
            'size "%s" is invalid; width and/or height are not numbers' % s)
    return (int(w), int(h))

def interface(s):
    """
    Parses a string containing a host[:port] specification.
    """
    if not s:
        return None
    if ':' in s:
        host, port = s.split(':', 1)
        if not host:
            host = '0.0.0.0'
        if port.isdigit():
            port = int(port)
    else:
        host = s
        port = 80
    return (host, port)


class PicroscopyConsoleApp(object):
    def __init__(self):
        super().__init__()
        self.parser = argparse.ArgumentParser(
            description=__doc__,
            # suppress creation of unspecified attributes
            argument_default=argparse.SUPPRESS
            )
        self.parser.set_defaults(log_level=logging.WARNING)
        self.parser.add_argument('--version', action='version',
            version=__version__)
        self.parser.add_argument(
            '-c', '--config', dest='config', action='store',
            help='specify the configuration file to load')
        self.parser.add_argument(
            '-q', '--quiet', dest='log_level', action='store_const',
            const=logging.ERROR, help='produce less console output')
        self.parser.add_argument(
            '-v', '--verbose', dest='log_level', action='store_const',
            const=logging.INFO, help='produce more console output')
        self.parser.add_argument(
            '-l', '--log-file', dest='log_file', metavar='FILE', default=None,
            help='log messages to the specified file')
        self.parser.add_argument(
            '-P', '--pdb', dest='debug', action='store_true', default=False,
            help='run under PDB (debug mode)')
        self.parser.add_argument(
            '-G', '--gstreamer', dest='gstreamer', action='store_true',
            default=False, help='use GStreamer instead of raspivid/still - '
            'this is intended for debugging on a non-RPi platform')
        self.parser.add_argument(
            '-d', '--daemon', dest='daemon', action='store_true', default=False,
            help='run as a background daemon process')
        self.parser.add_argument(
            '-L', '--listen', dest='listen', action='store',
            default='0.0.0.0:80', metavar='HOST[:PORT]', type=interface,
            help='the address and port of the interface the web-server will '
            'listen on. Default: %(default)s')
        self.parser.add_argument(
            '--images-dir', dest='images_dir', action='store', metavar='DIR',
            help='the directory in which to store images taken by the camera.')
        self.parser.add_argument(
            '--thumbs-dir', dest='thumbs_dir', action='store', metavar='DIR',
            help='the directory in which to store the thumbnail of images '
            'taken by the camera.')
        self.parser.add_argument(
            '--thumbs-size', dest='thumbs_size', action='store',
            default='320x320', metavar='WIDTHxHEIGHT', type=size,
            help='the size that thumbnails should be generated at by the '
            'website. Default: %(default)s')
        self.parser.add_argument(
            '--email-from', dest='email_from', action='store',
            default='picroscopy', metavar='USER[@HOST]',
            help='the address from which email will appear to be sent. '
            'Default: %(default)s')
        email_group = self.parser.add_mutually_exclusive_group()
        email_group.add_argument(
            '--sendmail', dest='sendmail', action='store',
            default='/usr/sbin/sendmail', metavar='EXEC',
            help='use the specified sendmail binary to send email. '
            'Default: %(default)s')
        email_group.add_argument(
            '--smtp-server', dest='smtp_server', action='store',
            metavar='HOST[:PORT]', type=interface,
            help='send email directly using the specified SMTP smarthost '
            '(mutually exclusive with --sendmail)')
        self.parser.add_argument(
            '--raspivid', dest='raspivid', action='store',
            default='/usr/bin/raspivid', metavar='EXEC',
            help='the path to the raspivid binary. Default: %(default)s')
        self.parser.add_argument(
            '--raspistill', dest='raspistill', action='store',
            default='/usr/bin/raspistill', metavar='EXEC',
            help='the path to the raspistill binary. Default: %(default)s')

    def __call__(self, args=None):
        if args is None:
            args = sys.argv[1:]
        # Parse the --config argument only and read the configuration file
        conf_parser = argparse.ArgumentParser(add_help=False)
        conf_parser.add_argument(
            '-c', '--config', dest='config', action='store',
            help='specify the configuration file to load')
        conf_args, args = conf_parser.parse_known_args(args)
        if conf_args.config:
            config = configparser.ConfigParser(interpolation=None)
            logging.info('Reading configuration from %s' % conf_args.config)
            if not config.read(conf_args.config):
                self.parser.error(
                    'unable to read configuration file %s' % conf_args.config)
            self.parser.set_defaults(**config['picroscopy'])
        # Parse the rest of the arguments, overriding the config file
        args = self.parser.parse_args(args)
        # Configure the logging module according to args
        _CONSOLE.setLevel(args.log_level)
        if args.log_file:
            log_file = logging.FileHandler(args.log_file)
            log_file.setFormatter(
                logging.Formatter('%(asctime)s, %(levelname)s, %(message)s'))
            log_file.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(log_file)
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
        if args.debug:
            try:
                import pudb
            except ImportError:
                pudb = None
                import pdb
            return (pudb or pdb).runcall(self.main, args)
        else:
            try:
                return self.main(args) or 0
            except Exception as e:
                logging.error(str(e))
                return 1

    def main(self, args):
        app = PicroscopyWsgiApp(**vars(args))
        try:
            # XXX Print IP address in big font (display image? ascii art?)
            httpd = make_server(args.listen[0], args.listen[1], app)
            logging.warning('Listening on %s:%s' % (args.listen[0], args.listen[1]))
            httpd.serve_forever()
        finally:
            app.camera.close()
        return 0


main = PicroscopyConsoleApp()

if __name__ == '__main__':
    sys.exit(main())

