import os
import io
import re
import logging
import mimetypes
from wsgiref.util import FileWrapper

from webob import Request, Response, exc
from chameleon import PageTemplateLoader
from routes import Mapper

from picroscopy.camera import PicroscopyCamera


class PicroscopyWsgiApp(object):
    def __init__(self, images_dir, thumbs_dir, static_dir, templates_dir):
        super().__init__()
        self.camera = PicroscopyCamera(images_dir, thumbs_dir)
        self.static_dir = os.path.abspath(os.path.normpath(static_dir))
        self.templates_dir = os.path.abspath(os.path.normpath(templates_dir))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')
        self.layout = self.templates['layout']
        self.mapper = Mapper()
        self.mapper.connect('home',     '/', page='index',     handler='template')
        self.mapper.connect('template', '/{page}.html',        handler='template')
        self.mapper.connect('download', '/images.zip',         handler='download')
        self.mapper.connect('send',     '/send',               handler='send')
        self.mapper.connect('clear',    '/clear',              handler='clear')
        self.mapper.connect('static',   '/static/{path:.*?}',  handler='static')
        self.mapper.connect('image',    '/images/{image}.jpg', handler='image')
        self.mapper.connect('thumb',    '/thumbs/{image}.jpg', handler='thumb')

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            else:
                self.not_found(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def not_found(self, req):
        raise exc.HTTPNotFound(
            'The resource at %s could not be found' % req.path_info)

    def handle_image(self, req):
        """
        Serve an image from the camera library
        """
        image = req.path_info.rsplit('/', 1)[1]
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length, f = self.camera.open_image(image)
        resp.app_iter = FileWrapper(f)
        return resp

    def handle_thumb(self, req):
        """
        Serve a thumbnail of an image frmo the camera library
        """
        image = req.path_info.rsplit('/', 1)[1]
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length, f = self.camera.open_thumbnail(image)
        resp.app_iter = FileWrapper(f)
        return resp

    def handle_static(self, req):
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
        resp.app_iter = FileWrapper(io.open(path, 'rb'))
        return resp

    def handle_template(self, req):
        """
        Serve a Chameleon template-based page
        """
        path = req.path_info[1:-len('.html')]
        resp = Response()
        resp.content_type = 'text/html'
        resp.content_encoding = 'utf-8'
        try:
            template = self.templates[path]
        except ValueError:
            self.not_found(req)
        resp.text = template(
            layout=self.layout,
            camera=self.camera,
            url=req.environ['routes.url'])
        return resp

