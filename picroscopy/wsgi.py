import os
import io
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


class PicroscopyWsgiApp(object):
    def __init__(self, images_dir, static_dir, templates_dir):
        self.images_dir = os.path.abspath(os.path.normpath(images_dir))
        self.static_dir = os.path.abspath(os.path.normpath(static_dir))
        self.templates_dir = os.path.abspath(os.path.normpath(templates_dir))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            if req.path_info.startswith('/static/'):
                resp = self.static(req, req.path_info[len('/static/'):])
            else:
                resp = self.index(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def static(self, request, path):
        """
        Serve static files from disk
        """
        resolved_path = os.path.normpath(os.path.join(self.static_dir, path))
        if not resolved_path.startswith(self.static_dir):
            raise exc.HTTPNotFound(
                'The resource at %s could not be found' % path)
        response = Response()
        response.content_type, response.content_encoding = mimetypes.guess_type(
                resolved_path, strict=False)
        if response.content_type is None:
            response.content_type = 'application/octet-stream'
        response.content_length = os.stat(resolved_path).st_size
        response.app_iter = FileIterator(io.open(resolved_path, 'rb'))
        return response

    def index(self, request):
        template = self.templates['index']
        return Response(template())

    def take_picture(self, request):
        pass

    def delete_pictures(self, request):
        pass

    def send_archive(self, request):
        pass

