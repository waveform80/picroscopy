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
This module defines the interface to the Pi's camera. Primarily this is derived
from the `picamera`_ package, but the base class, :class:`picamera.PiCamera`,
is extended to draw scale bars on taken images and calibrate said scales.

.. _picamera: http://pypi.python.org/pypi/picamera/
"""

import os
import io
import tempfile
import bisect
import logging
import subprocess

from PIL import Image, ImageDraw
from picamera import PiCamera

class PicroscopyCamera(PiCamera):

    scale_styles = [
        'white_bar',
        'black_bar',
        'checked_bar',
        'white_axis',
        'black_axis',
        ]

    def __init__(self, **kwargs):
        super().__init__()
        self.lenses = {}
        self._lens = None
        self.scale_bar = kwargs.get('scale_bar', False)
        self.scale_position = kwargs.get('scale_position', 9)
        self.scale_style = kwargs.get('scale_style', 'white_bar')

    def capture(self, output, format=None, **options):
        # No matter what format is requested, capture the image as JPEG at
        # quality 95. This is to ensure we get the EXIF data. We then pull out
        # the EXIF data with exiftool, perform any image manipulation and
        # conversion we want with PIL, save it (losing the EXIF data as PIL
        # doesn't preserve it) and then get exiftool to restore it back again
        image_stream = io.BytesIO()
        super().capture(image_stream, 'jpeg', quality=95)
        image_stream.seek(0)
        _, exif = tempfile.mkstemp(suffix='.exif')
        try:
            self._export_exif(image_stream, exif)
            image_stream.seek(0)
            img = Image.open(image_stream)
            if self.scale_bar:
                self._draw_scale_bar(img)
            if format is not None:
                img.save(output, format.upper(), **options)
            else:
                img.save(output, **options)
            self._import_exif(output, exif)
        finally:
            os.unlink(exif)

    def _export_exif(self, image, exif):
        # XXX Yes, this introduces a race condition, but when using -o exiftool
        # refuses to overwrite an existing output file (even if
        # -overwrite_output is specified, despite what the docs say...)
        os.unlink(exif)
        p = subprocess.Popen(
            ['exiftool', '-o', exif, '-all:all', '-'],
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None,
            bufsize=-1)
        p.communicate(image.read())
        assert p.returncode == 0
        image.seek(0)

    def _import_exif(self, image, exif):
        p = subprocess.Popen(
            ['exiftool', '-tagsFromFile', exif, '-overwrite_original', image])
        p.communicate()
        assert p.returncode == 0

    def _draw_scale_bar(self, image):
        # The image is divided into thirds like so, with the corresponding
        # values of scale_position:
        #
        #   +---------+---------+---------+
        #   |   ###   |   ###   |   ###   |
        #   |    1    |    2    |    3    |
        #   |         |         |         |
        #   +---------+---------+---------+
        #   |         |         |         |
        #   |   #4#   |   #5#   |   #6#   |
        #   |         |         |         |
        #   +---------+---------+---------+
        #   |         |         |         |
        #   |    7    |    8    |    9    |
        #   |   ###   |   ###   |   ###   |
        #   +---------+---------+---------+
        #
        # The width of a cell is divided by 14 (hence the width of the
        # image by 42 as 14*3=42) and this unit forms the basis of the
        # scale bar. The scale bar is made as close to 10 units wide as
        # possible (for a reasonable value of the scale) and is 1 unit
        # high.
        scales = [
            1, 2, 3, 4, 5,
            10, 15, 20, 25,
            30, 40, 50, 75,
            100, 150, 200, 250,
            300, 400, 500, 750,
            ]
        draw = ImageDraw.Draw(image)
        w, h = img.size
        unit = w / 42
        scale_w = (1 / self.scale) * unit * 10
        label = scales[bisect.bisect_left(scales, scale_w) - 1]
        scale_w = label * self.scale
        xcell = (self.scale_position - 1) % 3
        ycell = (self.scale_position - 1) // 3
        left = ((xcell * 14) + 2) * unit
        right = left + (unit * 10)
        bottom = (
            unit * 2               if ycell == 0 else
            (h // 2) - (unit // 2) if ycell == 1 else
            h - unit * 2          #if ycell == 2
            )
        top = bottom - unit
        if self.scale_style == 'white_bar':
            draw.rectangle((left, top, right, bottom), outline='#000000', fill='#ffffff')
        elif self.scale_style == 'black_bar':
            draw.rectangle((left, top, right, bottom), otuline='#ffffff', fill='#000000')
        else:
            raise NotImplementedError

    def _get_lens(self):
        return self._lens
    def _set_lens(self, value):
        if value is not None and value not in self.lenses:
            raise ValueError('Unknown lens %s' % value)
        self._lens = value

    @property
    def scale(self):
        if self.lens is None:
            return None
        return self.lenses[self.lens]
