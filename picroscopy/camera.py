import os
import io
import logging
import threading
import subprocess
import itertools

from PIL import Image


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

def launch_gst(pipeline):
    cmdline = ['gst-launch-0.10'] + [
        param
        for elem in zip(pipeline, itertools.cycle('!'))
        for param in elem
        ][:-1]
    return subprocess.Popen(cmdline)


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
            and os.path.isfile(os.path.join(self.images_dir, f))
            )

    def __iter__(self):
        for f in os.listdir(self.images_dir):
            if (
                    f.endswith('.jpg') and
                    os.path.isfile(os.path.join(self.images_dir, f))
                    ):
                yield f

    def __contains__(self, value):
        return (
            value.endswith('.jpg') and
            os.path.isfile(os.path.join(self.images_dir, value))
            )

    def _start_preview(self):
        if self.video_process:
            raise ValueError('Video preview already started')
        self.video_process = launch_gst(VIDEO_PREVIEW)

    def _stop_preview(self):
        if self.video_process:
            self.video_process.terminate()
            self.video_process.wait()
            self.video_process = None

    def capture(self):
        with self.capture_lock.acquire():
            self._stop_preview()
            try:
                capture_process = launch_gst(IMAGE_CAPTURE)
                capture_process.communicate()
            finally:
                self._start_preview()

    def clear(self):
        for f in os.listdir(self.images_dir):
            if f.endswith('.jpg') and os.path.isfile(f):
                os.unlink(os.path.join(self.images_dir, f))

    def open_image(self, image):
        if not image in self:
            raise ValueError('Invalid image %s' % image)
        image = os.path.join(self.images_dir, image)
        return os.stat(image).st_mtime, io.open(image, 'rb')

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
        return os.stat(thumb).st_mtime, io.open(thumb, 'rb')

    def _generate_thumbnail(self, image, thumb):
        im = Image.open(image)
        im.thumbnail(self.thumbs_size, Image.ANTIALIAS)
        im.save(thumb, optimize=True, progressive=True)

