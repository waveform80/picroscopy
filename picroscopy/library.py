# vim: set et sw=4 sts=4 fileencoding=utf-8:

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
This module defines the library that stores pictures taken by the Pi's camera.
The main class is :class:`PicroscopyLibrary` which encapsulates the camera
object, and provides an iterable view of the pictures taken by the camera.

Methods are provided to :meth:`~PicroscopyLibrary.capture` images, to
:meth:`~PicroscopyLibrary.clear` the library, and to
:meth:`~PicroscopyLibrary.archive` or :meth:`~PicroscopyLibrary.send` the
contents of the library. As suggested above, iterating over the library returns
the filenames of the images that have been captured, while methods like
:meth:`~PicroscopyLibrary.stat_image`, :meth:`~PicroscopyLibrary.open_image`,
and :meth:`~PicroscopyLibrary.open_thumbnail` can be called with these
filenames to obtain the metadata or data of the images.
"""

import os
import io
import errno
import logging
import datetime
import tempfile
import zipfile
import smtplib
import subprocess
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from PIL import Image

from picroscopy import __version__
from picroscopy.exif import format_exif
from picroscopy.camera import PicroscopyCamera


HERE = os.path.abspath(os.path.dirname(__file__))

def ascii_property(value, name):
    try:
        value.encode('ascii')
    except UnicodeEncodeError:
        raise ValueError('Non-ASCII characters not permitted in %s' % name)
    return value


class PicroscopyLibrary(object):

    format_extensions = {
        'jpeg': '.jpg',
        'tiff': '.tiff',
        'png':  '.png',
        }

    extensions = tuple(format_extensions.values())

    def __init__(self, **kwargs):
        super().__init__()
        self.camera = PicroscopyCamera(**kwargs)
        self.images_tmp = tempfile.mkdtemp(dir=os.environ.get('TEMP', '/tmp'))
        self.thumbs_tmp = tempfile.mkdtemp(dir=os.environ.get('TEMP', '/tmp'))
        self.images_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'images_dir', self.images_tmp)))
        logging.info('Images directory: %s', self.images_dir)
        self.thumbs_dir = os.path.abspath(os.path.normpath(kwargs.get(
            'thumbs_dir', self.thumbs_tmp)))
        logging.info('Thumbnails directory: %s', self.thumbs_dir)
        try:
            os.mkdir(self.images_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        try:
            os.mkdir(self.thumbs_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        self.thumbs_size = kwargs.get('thumbs_size', (320, 320))
        logging.info('Generating thumbnails at %d x %d', *self.thumbs_size)
        self.email_from = kwargs.get('email_from', 'picroscopy')
        logging.info('Sending mail from: %s', self.email_from)
        self.sendmail = kwargs.get('sendmail', '/usr/sbin/sendmail')
        self.smtp_server = kwargs.get('smtp_server', None)
        if self.smtp_server:
            logging.info('Sending mail via SMTP server: %s', self.smtp_server)
        else:
            logging.info('Sending mail via sendmail binary: %s', self.sendmail)
        self.camera_reset()
        self.user_reset()
        self.camera.start_preview()

    def close(self):
        self.camera.stop_preview()
        self.camera.close()
        if self.images_dir == self.images_tmp:
            self.clear()
        os.rmdir(self.images_tmp)
        os.rmdir(self.thumbs_tmp)

    def __len__(self):
        return sum(1 for f in os.listdir(self.images_dir) if f.endswith(self.extensions))

    def __iter__(self):
        for f in sorted(os.listdir(self.images_dir)):
            if f.endswith(self.extensions):
                yield f

    def __contains__(self, value):
        return (
            value.endswith(self.extensions) and
            os.path.exists(os.path.join(self.images_dir, value))
            )

    def camera_reset(self):
        self.camera.sharpness = 0
        self.camera.contrast = 0
        self.camera.brightness = 50
        self.camera.saturation = 0
        # XXX Bug in the camera: ISO needs to be zero for exposure mode to work
        self.camera.ISO = 0
        self.camera.exposure_compensation = 0
        self.camera.hflip = False
        self.camera.vflip = False
        self.camera.exposure_mode = 'auto'
        self.camera.awb_mode = 'auto'
        self.camera.meter_mode = 'average'
        self.software = 'Picroscopy %s' % __version__

    def user_reset(self):
        self.description = ''
        self.artist = ''
        self.copyright = ''
        self.email = ''
        self.format = 'jpeg'
        self.filename_template = 'pic-{date:%Y%m%d}-{counter:05d}{ext}'
        self.counter = 1

    def _get_description(self):
        return self.camera.exif_tags.get('IFD0.ImageDescription', '')
    def _set_description(self, value):
        if value:
            self.camera.exif_tags['IFD0.ImageDescription'] = ascii_property(value, 'Description')
        else:
            self.camera.exif_tags.pop('IFD0.ImageDescription', '')
    description = property(_get_description, _set_description)

    def _get_artist(self):
        return self.camera.exif_tags.get('IFD0.Artist', '')
    def _set_artist(self, value):
        if value:
            self.camera.exif_tags['IFD0.Artist'] = ascii_property(value, 'Name')
        else:
            self.camera.exif_tags.pop('IFD0.Artist', '')
    artist = property(_get_artist, _set_artist)

    def _get_email(self):
        return self._email
    def _set_email(self, value):
        self._email = ascii_property(value, 'Email')
    email = property(_get_email, _set_email)

    def _get_copyright(self):
        return self.camera.exif_tags.get('IFD0.Copyright', '')
    def _set_copyright(self, value):
        if value:
            self.camera.exif_tags['IFD0.Copyright'] = ascii_property(value, 'Copyright')
        else:
            self.camera.exif_tags.pop('IFD0.Copyright', '')
    copyright = property(_get_copyright, _set_copyright)

    def _get_software(self):
        return self.camera.exif_tags.get('IFD0.Software', '')
    def _set_software(self, value):
        if value:
            self.camera.exif_tags['IFD0.Software'] = ascii_property(value, 'Software')
        else:
            self.camera.exif_tags.pop('IFD0.Software', '')
    software = property(_get_software, _set_software)

    def _get_filename_template(self):
        return self._filename_template
    def _set_filename_template(self, value):
        try:
            value.format(counter=1, date=datetime.datetime.now(), ext='.jpg')
        except KeyError as e:
            raise ValueError('Unknown value %s in template' % e)
        self._filename_template = value
    filename_template = property(_get_filename_template, _set_filename_template)

    def capture(self):
        # Safely allocate a new filename for the image
        date = datetime.datetime.now()
        ext = self.format_extensions[self.format]
        while True:
            filename = os.path.join(
                self.images_dir,
                self.filename_template.format(
                    date=date, counter=self.counter, ext=ext)
                )
            try:
                # XXX mode 'x' is only available in Py3.3+
                fd = os.open(filename, os.O_CREAT | os.O_EXCL)
            except OSError:
                self.counter += 1
            else:
                os.close(fd)
                break
        self.camera.capture(filename, self.format)

    def remove(self, image):
        try:
            os.unlink(os.path.join(self.images_dir, image))
        except OSError:
            raise KeyError(image)
        try:
            os.unlink(os.path.join(self.thumbs_dir, image))
        except OSError as e:
            if e.errno != 2:
                raise

    def clear(self):
        for f in self:
            self.remove(f)

    def archive(self):
        data = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)
        # DEFLATE is basically ineffective with JPEGs, so use STORED
        with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_STORED) as archive:
            for f in self:
                archive.write(os.path.join(self.images_dir, f), f)
        data.seek(0)
        return data

    def send(self, address=None):
        if address is None:
            address = self.email
        if not address:
            raise ValueError('No e-mail address specified')
        # Construct the multi-part email message
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = address
        msg['Subject'] = 'Picroscopy: %d image(s)' % len(self)
        body = [
            'Please find attached %d image(s) from Picroscopy:' % len(self),
            '',
            ]
        body.extend(image for image in self)
        body = '\n'.join(body)
        msg.attach(MIMEText(body))
        for image in self:
            f = self.open_image(image)
            msg.attach(MIMEImage(f.read()))
        if self.smtp_server:
            s = smtplib.SMTP(*self.smtp_server)
            s.send_message(msg)
            s.quit()
        else:
            with subprocess.Popen(
                    [self.sendmail, '-t', '-oi'], stdin=subprocess.PIPE) as proc:
                proc.communicate(msg.as_string().encode('ascii'))

    def stat_image(self, image):
        if not image in self:
            raise KeyError(image)
        return os.stat(os.path.join(self.images_dir, image))

    def open_image(self, image):
        if not image in self:
            raise KeyError(image)
        return io.open(os.path.join(self.images_dir, image), 'rb')

    def open_image_exif(self, image):
        if not image in self:
            raise KeyError(image)
        image = os.path.join(self.images_dir, image)
        p = subprocess.Popen(
            ['exiftool', '-j', image],
            stdin=None, stdout=subprocess.PIPE, stderr=None,
            bufsize=-1)
        out, err = p.communicate()
        assert p.returncode == 0
        return json.loads(out.decode('utf-8'))[0]

    def stat_thumbnail(self, image):
        if not image in self:
            raise KeyError(image)
        self._generate_thumbnail(image)
        return os.stat(os.path.join(self.thumbs_dir, image))

    def open_thumbnail(self, image):
        if not image in self:
            raise KeyError(image)
        self._generate_thumbnail(image)
        return io.open(os.path.join(self.thumbs_dir, image), 'rb')

    def _generate_thumbnail(self, image):
        thumb = os.path.join(self.thumbs_dir, image)
        image = os.path.join(self.images_dir, image)
        if (
                not os.path.exists(thumb) or
                os.stat(thumb).st_mtime < os.stat(image).st_mtime
                ):
            im = Image.open(image)
            im.thumbnail(self.thumbs_size, Image.ANTIALIAS)
            im.save(thumb, format='JPEG', optimize=True, progressive=True)

