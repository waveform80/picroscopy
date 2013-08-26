#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import subprocess
import locale
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

class PicroscopyConsoleApp(object):
    def __init__(self):
        super().__init__()
        self.parser = argparse.ArgumentParser(
            description=__doc__,
        )
        self.parser.add_argument('--version', action='version',
            version=__version__)
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
            '-d', '--daemon', dest='daemon', action='store_const', const=True,
            help='run as a background daemon process')
        self.parser.add_argument(
            '-p', '--port', dest='port', action='store',
            help='the port the web-server will listen on. Default: %(default)s')
        self.parser.add_argument(
            '-a', '--address', dest='address', action='store', metavar='HOST',
            help='the address of the interface the web-server will listen on. '
            'Specify 0.0.0.0 to listen on all interfaces. Default: %(default)s')
        self.parser.add_argument(
            '--images-dir', dest='images_dir', action='store',
            metavar='DIR', help='the directory in which to store images '
            'taken with the camera. Default: %(default)s')
        self.parser.add_argument(
            '--thumbnails-dir', dest='thumbs_dir', action='store',
            metavar='DIR', help='the directory in which to store thumbnail '
            'images taken by the website. Default: %(default)s')
        self.parser.add_argument(
            '--templates-dir', dest='templates_dir', action='store',
            metavar='DIR', help='the directory from which to read the '
            'website templates. Default: %(default)s')
        self.parser.add_argument(
            '--static-dir', dest='static_dir', action='store', metavar='DIR',
            help='the directory from which to read the static website files. '
            'Default: %(default)s')
        self.parser.add_argument(
            '--thumbnails-size', dest='thumbs_size', action='store',
            metavar='WxH',
            type=lambda s: [int(i) for i in s.split('x', 1)],
            help='the size that thumbnails should be generated at by the '
            'website. Default: %(default)s')
        self.parser.add_argument(
            '-P', '--pdb', dest='debug', action='store_true',
            help='run under PDB (debug mode)')
        self.parser.set_defaults(
            debug=False,
            log_level=logging.WARNING,
            log_file=None,
            daemon=False,
            address='127.0.0.1',
            port=8000,
            thumbs_size='320x320',
            thumbs_dir=os.path.join(HERE, 'data', 'thumbs'),
            images_dir=os.path.join(HERE, 'data', 'images'),
            templates_dir=os.path.join(HERE, 'templates'),
            static_dir=os.path.join(HERE, 'static'),
            )

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
            import pudb
            return pudb.runcall(self.main, args)
        else:
            try:
                return self.main(args) or 0
            except Exception as e:
                logging.error(str(e))
                return 1

    def main(self, args):
        httpd = make_server(
            args.address, args.port,
            PicroscopyWsgiApp(
                images_dir=args.images_dir,
                thumbs_dir=args.thumbs_dir,
                thumbs_size=args.thumbs_size,
                static_dir=args.static_dir,
                templates_dir=args.templates_dir,
                )
            )
        try:
            logging.info('Serving on http://%s:%s' % (args.address, args.port))
            httpd.serve_forever()
        finally:
            httpd.application.camera.close()
        return 0


main = PicroscopyConsoleApp()

if __name__ == '__main__':
    sys.exit(main())

