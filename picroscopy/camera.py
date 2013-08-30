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

from picroscopy import __version__
from picroscopy.exif import format_exif


HERE = os.path.abspath(os.path.dirname(__file__))

CAMERA_LOCK = threading.RLock()
PREVIEW_PROCESS = None
USE_GSTREAMER = False
RASPIVID = '/usr/bin/raspivid'
RASPISTILL = '/usr/bin/raspistill'


def raspi_settings(settings, exif=False):
    result = [
        '--sharpness',  str(settings.sharpness),
        '--contrast',   str(settings.contrast),
        '--brightness', str(settings.brightness),
        '--saturation', str(settings.saturation),
        '--ISO',        str(settings.ISO),
        '--ev',         str(settings.evcomp),
        '--exposure',   settings.exposure,
        '--metering',   settings.metering,
        '--awb',        settings.white_balance,
        ]
    if settings.vstab:
        result.append('--vstab')
    if settings.hflip:
        result.append('--hflip')
    if settings.vflip:
        result.append('--vflip')
    if exif:
        if settings.artist and settings.email:
            artist = '%s <%s>' % settings.artist
        else:
            artist = settings.artist
        if settings.software:
            result.extend(['-x', 'IFD0.Software=%s' % settings.software])
        if artist:
            result.extend(['-x', 'IFD0.Artist=Photographer, %s' % artist])
        if settings.copyright:
            result.extend(['-x', 'IFD0.Copyright=%s' % settings.copyright])
        elif settings.artist:
            result.extend(['-x', 'IFD0.Copyright=Copyright, %s, %d' % (
                artist, datetime.date.today().year)])
        if settings.description:
            result.extend(['-x', 'IFD0.ImageDescription=%s' % settings.description])
    return result

def start_preview(settings):
    global PREVIEW_PROCESS
    with CAMERA_LOCK:
        if not PREVIEW_PROCESS:
            if USE_GSTREAMER:
                cmdline = [
                    'gst-launch-0.10',
                    'v4l2src',                              '!',
                    'video/x-raw-yuv,width=320,height=240', '!',
                    'ffmpegcolorspace',                     '!',
                    'xvimagesink',
                    ]
            else:
                cmdline = [RASPIVID, '-t', '0'] + raspi_settings(settings)
            PREVIEW_PROCESS = subprocess.Popen(cmdline)

def stop_preview():
    global PREVIEW_PROCESS
    with CAMERA_LOCK:
        if PREVIEW_PROCESS:
            PREVIEW_PROCESS.terminate()
            PREVIEW_PROCESS.wait()
            PREVIEW_PROCESS = None

def capture_image(dest, settings):
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
                    '-t', '2000', # Allow 2 seconds for calibration
                    '-o', dest,
                    ] + raspi_settings(settings, exif=True)
            p = subprocess.Popen(cmdline)
            p.communicate()
        finally:
            start_preview(settings)

def int_property(value, min_value, max_value, name):
    value = int(value)
    if not (min_value <= value <= max_value):
        raise ValueError('Invalid %s: %d not between %d and %d' % (
            name, value, min_value, max_value))
    return value

def bool_property(value, name):
    value = bool(int(value))
    return bool(value)

def str_property(value, valid, name):
    if not value in valid:
        raise ValueError('Invalid %s: %s' % (name, value))
    return value

def ascii_property(value, name):
    try:
        value.encode('ascii')
    except UnicodeEncodeError:
        raise ValueError('Non-ASCII characters not permitted in %s' % name)
    return value


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
        self.camera_reset()
        self.user_reset()
        start_preview(self)

    def close(self):
        stop_preview()

    def restart(self):
        stop_preview()
        start_preview(self)

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

    def camera_reset(self):
        self._sharpness = 0
        self._contrast = 0
        self._brightness = 50
        self._saturation = 0
        self._ISO = 400
        self._evcomp = 0
        self._vstab = False
        self._hflip = False
        self._vflip = False
        self._exposure = 'auto'
        self._white_balance = 'auto'
        self._metering = 'average'
        self._software = 'Picroscopy %s' % __version__

    def user_reset(self):
        self._description = ''
        self._artist = ''
        self._email = ''
        self._copyright = ''
        self.counter = 1

    def _get_sharpness(self):
        return self._sharpness
    def _set_sharpness(self, value):
        self._sharpness = int_property(value, -100, 100, 'Sharpness')
    sharpness = property(_get_sharpness, _set_sharpness)

    def _get_contrast(self):
        return self._contrast
    def _set_contrast(self, value):
        self._contrast = int_property(value, -100, 100, 'Contrast')
    contrast = property(_get_contrast, _set_contrast)

    def _get_brightness(self):
        return self._brightness
    def _set_brightness(self, value):
        self._brightness = int_property(value, 0, 100, 'Brightness')
    brightness = property(_get_brightness, _set_brightness)

    def _get_saturation(self):
        return self._saturation
    def _set_saturation(self, value):
        self._saturation = int_property(value, -100, 100, 'Saturation')
    saturation = property(_get_saturation, _set_saturation)

    def _get_ISO(self):
        return self._ISO
    def _set_ISO(self, value):
        self._ISO = int_property(value, 100, 800, 'ISO')
    ISO = property(_get_ISO, _set_ISO)

    def _get_evcomp(self):
        return self._evcomp
    def _set_evcomp(self, value):
        self._evcomp = int_property(value, -10, 10, 'EV compensation')
    evcomp = property(_get_evcomp, _set_evcomp)

    def _get_exposure(self):
        return self._exposure
    def _set_exposure(self, value):
        self._exposure = str_property(value, (
            #'off',
            'auto',
            'night',
            'nightpreview',
            'backlight',
            'spotlight',
            'sports',
            'snow',
            'beach',
            #'verylong',
            'fixedfps',
            'antishake',
            'fireworks',
            ), 'Exposure')
    exposure = property(_get_exposure, _set_exposure)

    def _get_white_balance(self):
        return self._white_balance
    def _set_white_balance(self, value):
        self._white_balance = str_property(value, (
            'off',
            'auto',
            'sun',
            'cloud',
            'shade',
            'tungsten',
            'fluorescent',
            'incandescent',
            'flash',
            'horizon',
            ), 'White balance')
    white_balance = property(_get_white_balance, _set_white_balance)

    def _get_metering(self):
        return self._metering
    def _set_metering(self, value):
        self._metering = str_property(value, (
            'average',
            'spot',
            'backlit',
            'matrix',
            ), 'Metering')
    metering = property(_get_metering, _set_metering)

    def _get_vstab(self):
        return self._vstab
    def _set_vstab(self, value):
        self._vstab = bool_property(value, 'Video stabilization')
    vstab = property(_get_vstab, _set_vstab)

    def _get_hflip(self):
        return self._hflip
    def _set_hflip(self, value):
        self._hflip = bool_property(value, 'Horizontal flip')
    hflip = property(_get_hflip, _set_hflip)

    def _get_vflip(self):
        return self._vflip
    def _set_vflip(self, value):
        self._vflip = bool_property(value, 'Vertical flip')
    vflip = property(_get_vflip, _set_vflip)

    def _get_description(self):
        return self._description
    def _set_description(self, value):
        self._description = ascii_property(value, 'Description')
    description = property(_get_description, _set_description)

    def _get_artist(self):
        return self._artist
    def _set_artist(self, value):
        self._artist = ascii_property(value, 'Photographer')
    artist = property(_get_artist, _set_artist)

    def _get_email(self):
        return self._email
    def _set_email(self, value):
        self._email = ascii_property(value, 'Email')
    email = property(_get_email, _set_email)

    def _get_copyright(self):
        return self._copyright
    def _set_copyright(self, value):
        self._copyright = ascii_property(value, 'Copyright')
    copyright = property(_get_copyright, _set_copyright)

    def _get_software(self):
        return self._software
    def _set_software(self, value):
        self._software = ascii_property(value, 'Software')
    software = property(_get_software, _set_software)

    def capture(self):
        # Safely allocate a new filename for the image
        d = datetime.datetime.now().strftime('%Y%m%d')
        while True:
            filename = os.path.join(self.images_dir, 'PIC-%s-%04d.jpg' % (d, self.counter))
            try:
                # XXX mode 'x' is only available in Py3.3+
                fd = os.open(filename, os.O_CREAT | os.O_EXCL)
            except OSError:
                self.counter += 1
            else:
                os.close(fd)
                break
        capture_image(filename, self)

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
        im = Image.open(image)
        result = format_exif(im._getexif())
        result['Resolution'] = '%d x %d' % im.size
        return result

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
            im.save(thumb, optimize=True, progressive=True)

