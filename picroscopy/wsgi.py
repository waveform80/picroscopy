import os
import io
import re
import logging
import mimetypes
from wsgiref.util import FileWrapper

from webob import Request, Response, exc
from chameleon import PageTemplateLoader
from wheezy.routing import PathRouter, url

from picroscopy.camera import PicroscopyCamera

HERE = os.path.abspath(os.path.dirname(__file__))


class PicroscopyWsgiApp(object):
    def __init__(self, **kwargs):
        super().__init__()
        self.camera = PicroscopyCamera(
            kwargs.get('images_dir', os.path.join(HERE, 'data', 'images')),
            kwargs.get('thumbs_dir', os.path.join(HERE, 'data', 'thumbs')),
            kwargs.get('thumbs_size', (320, 320))
            )
        self.static_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'static_dir', os.path.join(HERE, 'static')
            )))
        self.templates_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'templates_dir', os.path.join(HERE, 'templates')
            )))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')
        self.layout = self.templates['layout']
        self.router = PathRouter()
        self.router.add_routes([
            url('/',                   self.do_template, kwargs={'page': 'index'}, name='home'),
            url('/{page}.html',        self.do_template, name='template'),
            url('/capture',            self.do_capture,  name='capture'),
            url('/images.zip',         self.do_download, name='download'),
            url('/send',               self.do_send,     name='send'),
            url('/clear',              self.do_clear,    name='clear'),
            url('/static/{path:any}',  self.do_static,   name='static'),
            url('/images/{image}.jpg', self.do_image,    name='image'),
            url('/thumbs/{image}.jpg', self.do_thumb,    name='thumb')
            ])

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            handler, kwargs = self.router.match(req.path_info)
            del kwargs['route_name']
            if handler:
                resp = handler(req, **kwargs)
            else:
                self.not_found(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def not_found(self, req):
        raise exc.HTTPNotFound(
            'The resource at %s could not be found' % req.path_info)

    def do_capture(self, req):
        pass

    def do_download(self, req):
        pass

    def do_send(self, req):
        pass

    def do_clear(self, req):
        pass

    def do_image(self, req, image):
        """
        Serve an image from the camera library
        """
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length, f = self.camera.open_image(image)
        resp.app_iter = FileWrapper(f)
        return resp

    def do_thumb(self, req, image):
        """
        Serve a thumbnail of an image from the camera library
        """
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length, f = self.camera.open_thumbnail(image)
        resp.app_iter = FileWrapper(f)
        return resp

    def do_static(self, req, path):
        """
        Serve static files from disk
        """
        path = os.path.normpath(os.path.join(self.static_dir, path))
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

    def do_template(self, req, page):
        """
        Serve a Chameleon template-based page
        """
        resp = Response()
        resp.content_type = 'text/html'
        resp.content_encoding = 'utf-8'
        try:
            template = self.templates[page]
        except ValueError:
            self.not_found(req)
        resp.text = template(
            layout=self.layout,
            camera=self.camera,
            router=self.router)
        return resp

