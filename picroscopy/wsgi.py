import os
import io
import re
import logging
import subprocess
import mimetypes

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


class FileIterator(object):
    """
    A fixed-size-block file iterator for use with Response.app_iter
    """
    def __init__(self, source, chunk_size=65536):
        self.source = source
        self.chunk_size = chunk_size

    def __iter__(self):
        while True:
            data = self.source.read(self.chunk_size)
            if not data:
                break
            yield data

    def close(self):
        self.source.close()


class PicroscopyImages(object):
    def __init__(self, source_dir):
        self.source_dir = source_dir

    def __len__(self):
        pass

    def __getitem__(self, index):
        pass


class PicroscopyWsgiApp(object):
    def __init__(self, images_dir, static_dir, templates_dir):
        self.static_dir = os.path.abspath(os.path.normpath(static_dir))
        self.images_dir = os.path.abspath(os.path.normpath(images_dir))
        self.images = PicroscopyImages(self.images_dir)
        self.templates_dir = os.path.abspath(os.path.normpath(templates_dir))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')
        self.layout = self.templates['layout']

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            if req.path_info.startswith('/static/'):
                resp = self.static(req)
            elif req.path_info.startswith('/images/'):
                resp = self.image(req)
            elif req.path_info.endswith('.html'):
                resp = self.template(req)
            else:
                self.not_found(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def not_found(self, req):
        raise exc.HTTPNotFound(
            'The resource at %s could not be found' % req.path_info)

    def image(self, req):
        image, ext = os.path.splitext(req.path_info.rsplit('/', 1)[1])
        # XXX Extend with support for PNG, TIF, etc.
        if ext != '.jpg':
            self.not_found(req)
        resp = Response()
        response.content_type = 'image/jpeg'
        response.content_length = os.stat(path).st_size
        try:
            resp.app_iter = FileIterator(io.open(path, 'rb'))
        except IOError as e:
            self.not_found(req)

    def static(self, req):
        """
        Serve static files from disk
        """
        path = os.path.normpath(
            os.path.join(self.static_dir, req.path_info[len('/static/'):]))
        if not path.startswith(self.static_dir):
            self.not_found(req)
        resp = Response()
        resp.content_type, resp.content_encoding = mimetypes.guess_type(
                path, strict=False)
        if resp.content_type is None:
            resp.content_type = 'application/octet-stream'
        resp.content_length = os.stat(path).st_size
        resp.app_iter = FileIterator(io.open(path, 'rb'))
        return resp

    def template(self, req):
        """
        Serve a template-based page
        """
        path = req.path_info[1:-len('.html')]
        resp = Response()
        resp.content_type = 'text/html'
        resp.content_encoding = 'utf-8'
        try:
            template = self.templates[path]
        except ValueError:
            self.not_found(req)
        resp.text = template(layout=self.layout)
        return resp

