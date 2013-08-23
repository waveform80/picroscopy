import os
import logging
import subprocess

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

class PicroscopyWsgiApp(object):
    def __init__(self, images_dir, static_dir, templates_dir):
        self.images_dir = os.path.abspath(os.path.normpath(images_dir))
        self.static_dir = os.path.abspath(os.path.normpath(static_dir))
        self.templates_dir = os.path.abspath(os.path.normpath(templates_dir))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')

    def __call__(self, environ, start_response):
        req = Request(environ)
        logging.warning(req.path_info)
        try:
            resp = self.index(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def index(self, request):
        template = self.templates['index']
        return Response(template())

    def take_picture(self, request):
        pass

    def delete_pictures(self, request):
        pass

    def send_archive(self, request):
        pass

