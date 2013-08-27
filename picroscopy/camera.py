import os
import io
import logging
import threading
import subprocess
import datetime
import tempfile
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from PIL import Image

HERE = os.path.abspath(os.path.dirname(__file__))

CAMERA_LOCK = threading.Lock()
VIDEO_PROCESS = None
USE_GSTREAMER = False
RASPIVID = '/usr/bin/raspivid'
RASPISTILL = '/usr/bin/raspistill'


def start_preview():
    global VIDEO_PROCESS
    if not VIDEO_PROCESS:
        if USE_GSTREAMER:
            cmdline = [
                'gst-launch-0.10',
                'v4l2src',                              '!',
                'video/x-raw-yuv,width=320,height=240', '!',
                'ffmpegcolorspace',                     '!',
                'xvimagesink',
                ]
        else:
            cmdline = [RASPIVID, '-t', '0']
        VIDEO_PROCESS = subprocess.Popen(cmdline)

def stop_preview():
    global VIDEO_PROCESS
    if VIDEO_PROCESS:
        VIDEO_PROCESS.terminate()
        VIDEO_PROCESS.wait()
        VIDEO_PROCESS = None

def capture_image(dest):
    with CAMERA_LOCK:
        stop_preview()
        try:
            if USE_GSTREAMER:
                cmdline = [
                    'gst-launch-0.10',
                    'v4l2src', 'num-buffers=1',             '!',
                    'video/x-raw-yuv,width=640,height=480', '!',
                    'ffmpegcolorspace',                     '!',
                    'jpegenc',                              '!',
                    'filesink', 'location=%s' % dest,
                    ]
            else:
                cmdline = [
                    RASPISTILL,
                    '-t', '2',
                    '-o', dest,
                    ]
            p = subprocess.Popen(cmdline)
            p.communicate()
        finally:
            start_preview()


class PicroscopyCamera(object):
    def __init__(self, **kwargs):
        super().__init__()
        global USE_GSTREAMER, RASPIVID, RASPISTILL
        self.images_dir = kwargs.get(
            'images_dir', os.path.join(HERE, 'data', 'images'))
        self.thumbs_dir = kwargs.get(
            'thumbs_dir', os.path.join(HERE, 'data', 'thumbs'))
        if not os.path.exists(self.images_dir):
            raise ValueError(
                'The images directory %s does not exist' % self.images_dir)
        if not os.path.exists(self.thumbs_dir):
            raise ValueError(
                'The thumbnails directory %s does not exist' % self.thumbs_dir)
        self.thumbs_size = kwargs.get('thumbs_size', (320, 320))
        self.email_from = kwargs.get('email_from', 'picroscopy')
        self.sendmail = kwargs.get('sendmail', '/usr/sbin/sendmail')
        self.smtp_server = kwargs.get('smtp_server', None)
        USE_GSTREAMER = kwargs.get('gstreamer', False)
        RASPIVID = kwargs.get('raspivid', '/usr/bin/raspivid')
        RASPISTILL = kwargs.get('raspistill', '/usr/bin/raspistill')
        start_preview()

    def close(self):
        stop_preview()

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

    def capture(self):
        capture_image(os.path.join(
            self.images_dir,
            datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S.jpg')
            ))

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

    def email(self, address):
        # Construct the multi-part email message
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = address
        msg['Subject'] = 'Picroscopy: %d image(s)' % len(self)
        body = ['Please find attached %d image(s) from Picroscopy:', '']
        body.extend(image for image in self)
        body = '\n'.join(body)
        msg.attach(MIMEText(body))
        for image in self:
            _, f = self.open_image(image)
            msg.attach(MIMEImage(f.read()))
        if self.smtp_server:
            s = smtplib.SMTP(*self.smtp_server)
            s.send_message(msg)
            s.quit()
        else:
            with subprocess.Popen(
                    [self.sendmail, '-t', '-oi'], stdin=subprocess.PIPE) as proc:
                proc.communicate(msg.as_string().encode('ascii'))

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

