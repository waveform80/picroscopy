"""
This module defines the Picroscopy WSGI application. See `PEP-3333`_ for
information on the WSGI specification. The main class in the module is
PicroscopyWsgiApp. This is typically launched by PicroscopyConsoleApp using
the WSGI reference implementation included in Python, but could equally well
be served by any WSGI interface (Apache, nginx, etc).

The web application is a trival affair (being a single-user web-app) which uses
`wheezy.routing`_ to handle URL dispatch, and `WebOb`_'s Request and Response classes
to ease construction of the responses. Chameleon templates are used for
constructing HTML pages.

.. PEP-3333: http://www.python.org/dev/peps/pep-3333/
.. wheezy.routing: http://pythonhosted.org/wheezy.routing/
.. WebOb: http://webob.org/
"""

import os
import io
import re
import math
import logging
import mimetypes
import datetime
from wsgiref.util import FileWrapper
from operator import itemgetter

from webob import Request, Response, exc
from chameleon import PageTemplateLoader
from wheezy.routing import PathRouter, url

from picroscopy.camera import PicroscopyCamera

HERE = os.path.abspath(os.path.dirname(__file__))


class WebHelpers(object):
    def __init__(self, camera):
        self.camera = camera

    def image_size(self, image):
        return self.format_size(
            self.camera.stat_image(image).st_size, 'B', binary=True)

    def image_created(self, image):
        return datetime.datetime.fromtimestamp(
            self.camera.stat_image(image).st_mtime).strftime('%H:%M:%S on %a, %d %b %Y')

    def image_exif(self, image):
        exif_data = self.camera.open_image_exif(image)
        return sorted(
            ((title, value) for (title, value) in exif_data.items()),
            key=itemgetter(0)
            )

    def format_size(self, size, unit, precision=1, binary=False):
        prefixes = ('', 'k', 'M', 'G', 'T', 'P', 'E', 'Z')
        if not binary:
            base = 1000
        else:
            base = 1024
        if size <= 0:
            i = 0
        else:
            i = int(math.log(size) / math.log(base))
            if i >= len(prefixes):
                i = len(prefixes) - 1
        size /= base**i
        return '{size:.{prec}f}{prefix}{unit}'.format(
                size=size,
                prec=precision,
                prefix=prefixes[i],
                unit=unit)


class PicroscopyWsgiApp(object):
    def __init__(self, **kwargs):
        super().__init__()
        self.camera = PicroscopyCamera(**kwargs)
        self.helpers = WebHelpers(self.camera)
        self.static_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'static_dir', os.path.join(HERE, 'static')
            )))
        self.templates_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'templates_dir', os.path.join(HERE, 'templates')
            )))
        self.templates = PageTemplateLoader(
            self.templates_dir, default_extension='.pt')
        self.layout = self.templates['layout']
        # No need to make flashes a per-session thing - it's a single user app!
        self.flashes = []
        self.router = PathRouter()
        self.router.add_routes([
            url('/',                   self.do_template, kwargs={'page': 'library'}, name='home'),
            url('/{page}.html',        self.do_template, name='template'),
            url('/view/{image}.html',  self.do_template, kwargs={'page': 'image'}, name='view'),
            url('/static/{path:any}',  self.do_static,   name='static'),
            url('/images/{image}',     self.do_image,    name='image'),
            url('/thumbs/{image}',     self.do_thumb,    name='thumb'),
            url('/delete/{image}',     self.do_delete,   name='delete'),
            url('/config',             self.do_config,   name='config'),
            url('/reset',              self.do_reset,    name='reset'),
            url('/capture',            self.do_capture,  name='capture'),
            url('/download',           self.do_download, name='download'),
            url('/send',               self.do_send,     name='send'),
            url('/logout',             self.do_logout,   name='logout'),
            ])

    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            handler, kwargs = self.router.match(req.path_info)
            if handler:
                # XXX Why does route_name only appear in kwargs sometimes?!
                if 'route_name' in kwargs:
                    del kwargs['route_name']
                resp = handler(req, **kwargs)
            else:
                self.not_found(req)
        except exc.HTTPException as e:
            # The exception itself is a WSGI response
            resp = e
        return resp(environ, start_response)

    def not_found(self, req):
        """
        Handler for unknown locations (404)
        """
        raise exc.HTTPNotFound(
            'The resource at %s could not be found' % req.path_info)

    def do_reset(self, req):
        """
        Reset the camera settings to their defaults
        """
        self.camera.camera_reset()
        self.camera.restart()
        self.flashes.append('Camera settings reset to defaults')
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='library'))

    def do_config(self, req):
        """
        Configure the camera settings
        """
        for setting in (
                'sharpness', 'contrast', 'brightness', 'saturation', 'ISO',
                'evcomp'):
            try:
                setattr(
                    self.camera, setting.replace('-', '_'),
                    int(req.params[setting])
                    )
            except ValueError:
                self.flashes.append(
                    'Invalid %s: %s' % (setting, req.params[setting]))
        for setting in ('vstab', 'hflip', 'vflip'):
            try:
                setattr(
                    self.camera, setting.replace('-', '_'),
                    req.params.get(setting, '0')
                    )
            except ValueError:
                self.flashes.append(
                    'Invalid %s: %s' % (setting, req.params[setting]))
        for setting in (
                'metering', 'white-balance', 'exposure', 'artist', 'email',
                'copyright', 'description', 'filename-template'):
            try:
                setattr(
                    self.camera, setting.replace('-', '_'),
                    req.params[setting]
                    )
            except ValueError:
                self.flashes.append(
                    'Invalid %s: %s' % (setting, req.params[setting]))
        # If any settings failed, re-render the settings form
        if self.flashes:
            return self.do_template(req, 'settings')
        self.camera.restart()
        self.flashes.append('Camera settings updated')
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='library'))

    def do_capture(self, req):
        """
        Take a new image with the camera and add it to the library
        """
        self.camera.capture()
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='library'))

    def do_download(self, req):
        """
        Send the camera library as a .zip archive
        """
        archive = self.camera.archive()
        size = archive.seek(0, io.SEEK_END)
        archive.seek(0)
        resp = Response()
        resp.content_type = 'application/zip'
        resp.content_length = size
        resp.content_disposition = 'attachment; filename=images.zip'
        resp.app_iter = FileWrapper(archive)
        return resp

    def do_send(self, req):
        """
        Send the camera library as a set of attachments to an email
        """
        self.camera.send()
        self.flashes.append('Email sent to %s' % camera.email)
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='library'))

    def do_delete(self, req, image):
        """
        Delete the selected images from camera library
        """
        self.camera.remove(image)
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='library'))

    def do_logout(self, req):
        """
        Clear the camera library of all images, reset all settings
        """
        self.camera.clear()
        self.camera.user_reset()
        self.camera.camera_reset()
        self.camera.restart()
        raise exc.HTTPFound(
            location=self.router.path_for('template', page='settings'))

    def do_image(self, req, image):
        """
        Serve an image from the camera library
        """
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length = self.camera.stat_image(image).st_size
        resp.app_iter = FileWrapper(self.camera.open_image(image))
        return resp

    def do_thumb(self, req, image):
        """
        Serve a thumbnail of an image from the camera library
        """
        if not image in self.camera:
            self.not_found(req)
        resp = Response()
        resp.content_type = 'image/jpeg'
        resp.content_length = self.camera.stat_thumbnail(image).st_size
        resp.app_iter = FileWrapper(self.camera.open_thumbnail(image))
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

    def do_template(self, req, page, image=None):
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
            req=req,
            page=page,
            image=image,
            helpers=self.helpers,
            layout=self.layout,
            flashes=self.flashes,
            camera=self.camera,
            router=self.router)
        del self.flashes[:]
        return resp

