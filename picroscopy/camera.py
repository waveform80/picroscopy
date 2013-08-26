import os
import io
import logging
import threading
import subprocess
import datetime
import tempfile
import zipfile

from PIL import Image


class PicroscopyCamera(object):
    def __init__(self, images_dir, thumbs_dir, thumbs_size=(320, 320)):
        super().__init__()
        if not os.path.exists(images_dir):
            raise ValueError('The images directory %s does not exist' % images_dir)
        if not os.path.exists(thumbs_dir):
            raise ValueError('The thumbnails directory %s does not exist' % thumbs_dir)
        self.images_dir = images_dir
        self.thumbs_dir = thumbs_dir
        self.thumbs_size = tuple(thumbs_size)
        self.capture_lock = threading.Lock()
        self.video_process = None
        self._start_preview()

    def close(self):
        self._stop_preview()

    def __len__(self):
        return sum(
            1 for f in os.listdir(self.images_dir)
            if f.endswith('.jpg')
            and os.path.exists(os.path.join(self.images_dir, f))
            )

    def __iter__(self):
        for f in sorted(os.listdir(self.images_dir)):
            if (
                    f.endswith('.jpg') and
                    os.path.exists(os.path.join(self.images_dir, f))
                    ):
                yield f

    def __contains__(self, value):
        return (
            value.endswith('.jpg') and
            os.path.exists(os.path.join(self.images_dir, value))
            )

    def _start_preview(self):
        if self.video_process:
            raise ValueError('Video preview already started')
        cmdline = [
            'gst-launch-0.10',
            'v4l2src',                              '!',
            'video/x-raw-yuv,width=320,height=240', '!',
            'ffmpegcolorspace',                     '!',
            'xvimagesink',
            ]
        self.video_process = subprocess.Popen(cmdline)

    def _stop_preview(self):
        if self.video_process:
            self.video_process.terminate()
            self.video_process.wait()
            self.video_process = None

    def capture(self):
        with self.capture_lock:
            self._stop_preview()
            try:
                image_filename = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S.jpg')
                image_filename = os.path.join(self.images_dir, image_filename)
                cmdline = [
                    'gst-launch-0.10',
                    'v4l2src', 'num-buffers=1',             '!',
                    'video/x-raw-yuv,width=640,height=480', '!',
                    'ffmpegcolorspace',                     '!',
                    'jpegenc',                              '!',
                    'filesink', 'location=%s' % image_filename,
                    ]
                print(repr(cmdline))
                capture_process = subprocess.Popen(cmdline)
                capture_process.communicate()
            finally:
                self._start_preview()

    def clear(self):
        for f in os.listdir(self.images_dir):
            image = os.path.join(self.images_dir, f)
            thumb = os.path.join(self.thumbs_dir, f)
            if f.endswith('.jpg') and os.path.exists(image):
                os.unlink(image)
                if os.path.exists(thumb):
                    os.unlink(thumb)

    def archive(self):
        data = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)
        # DEFLATE is basically ineffective with JPEGs, so use STORED
        with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_STORED) as archive:
            for f in self:
                archive.write(os.path.join(self.images_dir, f), f)
        data.seek(0)
        return data

    def open_image(self, image):
        if not image in self:
            raise ValueError('Invalid image %s' % image)
        image = os.path.join(self.images_dir, image)
        return os.stat(image), io.open(image, 'rb')

    def open_thumbnail(self, image):
        if not image in self:
            raise ValueError('Invalid image %s' % image)
        thumb = os.path.join(self.thumbs_dir, image)
        image = os.path.join(self.images_dir, image)
        if (
                not os.path.exists(thumb) or
                os.stat(thumb).st_mtime < os.stat(image).st_mtime
                ):
            self._generate_thumbnail(image, thumb)
        return os.stat(thumb), io.open(thumb, 'rb')

    def _generate_thumbnail(self, image, thumb):
        im = Image.open(image)
        im.thumbnail(self.thumbs_size, Image.ANTIALIAS)
        im.save(thumb, optimize=True, progressive=True)

