#!/usr/bin/env python3

import os
import io
import sys
import logging
import argparse
import subprocess
from wsgiref.simple_server import make_server

from webob import Request, Response, exc
from chameleon import PageTemplateLoader

# GStreamer pipeline for video preview
VIDEO_PREVIEW = [
    'v4l2src',
    'video/x-raw-yuv,width=640,height=480',
    'ffmpegcolorspace',
    'xvimagesink',
    ]

# GStreamer pipeline for image capture
IMAGE_CAPTURE = [
    'v4l2src num-buffers=1',
    'video/x-raw-yuv,width=640,height=480',
    'ffmpegcolorspace',
    'jpegenc',
    'filesink location=test.jpg',
    ]

class PicroscopyApp(object):
    def __init__(self, images_dir, templates_dir):
        self.images_dir = os.path.abspath(os.path.normpath(images_dir))
        self.templates_dir = os.path.abspath(os.path.normpath(templates_dir))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')

    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = Response(charset='utf8')
        methods = {
            'index':  self.index,
            'take':   self.take_picture,
            'delete': self.delete_pictures,
            'send':   self.send_archive,
            }
        try:
            methods.get(req.path_info, self.index)(req, resp)
        except exc.HTTPException, e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def index(self, request, response):
        template = self.templates['index']
        response.text = template()

    def take_picture(self, request, response):
        pass

    def delete_pictures(self, request, response):
        pass

    def send_archive(self, request, response):
        pass


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options = object()
    options.images_dir = '/home/dave/picroscopy/images'
    options.templates_dir = '/home/dave/picroscopy/templates'
    try:
        app = PicroscopyApp(options.images_dir, options.templates_dir)
        httpd = make_server('localhost', options.port, app)
        logging.info('Serving on http://localhost:%s' % options.port)
        httpd.serve_forever()
    except Exception as e:
        logging.error(str(e))
        return 1


if __name__ == '__main__':
    sys.exit(main())
