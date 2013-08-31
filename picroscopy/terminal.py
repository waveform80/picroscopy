#!/usr/bin/env python3

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
        )
        self.parser.set_defaults(
            debug=False,
            gstreamer=False,
            log_level=logging.WARNING,
            log_file=None,
            daemon=False,
            listen='0.0.0.0:80',
            thumbs_size='320x320',
            thumbs_dir=os.path.join(HERE, 'data', 'thumbs'),
            images_dir=os.path.join(HERE, 'data', 'images'),
            templates_dir=os.path.join(HERE, 'templates'),
            static_dir=os.path.join(HERE, 'static'),
            sendmail='/usr/sbin/sendmail',
            smtp_server='',
            email_from='picroscopy',
            raspivid='/usr/bin/raspivid',
            raspistill='/usr/bin/raspistill',
            )
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
            '-l', '--log-file', dest='log_file', metavar='FILE',
            help='log messages to the specified file')
        self.parser.add_argument(
            '-P', '--pdb', dest='debug', action='store_true',
            help='run under PDB (debug mode)')
        self.parser.add_argument(
            '-G', '--gstreamer', dest='gstreamer', action='store_true',
            help='use GStreamer instead of raspivid/still - this is '
            'intended for debugging on a non-RPi platform')
        self.parser.add_argument(
            '-d', '--daemon', dest='daemon', action='store_const', const=True,
            help='run as a background daemon process')
        self.parser.add_argument(
            '-L', '--listen', dest='listen', action='store',
            metavar='HOST[:PORT]', type=interface,
            help='the address and port of the interface the web-server will '
            'listen on. Default: %(default)s')
        self.parser.add_argument(
            '--images-dir', dest='images_dir', action='store',
            metavar='DIR',
            help='the directory in which to store images taken with the '
            'camera. Default: %(default)s')
        self.parser.add_argument(
            '--thumbnails-dir', dest='thumbs_dir', action='store',
            metavar='DIR',
            help='the directory in which to store thumbnail images taken '
            'by the website. Default: %(default)s')
        self.parser.add_argument(
            '--templates-dir', dest='templates_dir', action='store',
            metavar='DIR',
            help='the directory from which to read the website templates. '
            'Default: %(default)s')
        self.parser.add_argument(
            '--static-dir', dest='static_dir', action='store', metavar='DIR',
            help='the directory from which to read the static website files. '
            'Default: %(default)s')
        self.parser.add_argument(
            '--thumbnails-size', dest='thumbs_size', action='store',
            metavar='WIDTHxHEIGHT', type=size,
            help='the size that thumbnails should be generated at by the '
            'website. Default: %(default)s')
        self.parser.add_argument(
            '--email-from', dest='email_from', action='store',
            metavar='USER[@HOST]',
            help='the address from which email will appear to be sent. '
            'Default: %(default)s')
        email_group = self.parser.add_mutually_exclusive_group()
        email_group.add_argument(
            '--sendmail', dest='sendmail', action='store', metavar='PATH',
            help='use the specified sendmail binary to send email. '
            'Default: %(default)s')
        email_group.add_argument(
            '--smtp-server', dest='smtp_server', action='store',
            metavar='HOST[:PORT]', type=interface,
            help='send email directly using the specified SMTP smarthost '
            '(mutually exclusive with --sendmail)')
        self.parser.add_argument(
            '--raspivid', dest='raspivid', action='store', metavar='PATH',
            help='the path to the raspivid binary. Default: %(default)s')
        self.parser.add_argument(
            '--raspistill', dest='raspistill', action='store', metavar='PATH',
            help='the path to the raspistill binary. Default: %(default)s')

    def __call__(self, args=None):
        if args is None:
            args = sys.argv[1:]
        args = self.parser.parse_args(args)
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
            httpd = make_server(args.listen[0], args.listen[1], app)
            logging.warning('Listening on %s:%s' % (args.listen[0], args.listen[1]))
            httpd.serve_forever()
        finally:
            app.camera.close()
        return 0


main = PicroscopyConsoleApp()

if __name__ == '__main__':
    sys.exit(main())

