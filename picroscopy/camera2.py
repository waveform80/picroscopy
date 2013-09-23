#!/usr/bin/env python

from __future__ import (
    unicode_literals,
    print_function,
    division,
    absolute_import,
    )

import time
import ctypes as ct

import picroscopy.mmal as mmal
import picroscopy.bcm_host as bcm_host


class PiCameraError(Exception):
    """
    Base class for PiCamera errors
    """

class PiCameraRuntimeError(PiCameraError, RuntimeError):
    """
    Raised when an invalid sequence of operations is attempted with a PiCamera object
    """

class PiCameraValueError(PiCameraError, ValueError):
    """
    Raised when an invalid value is fed to a PiCamera object
    """



def camera_control_callback(port, buf):
    print("camera_control_callback")
    if buf[0].cmd != mmal.MMAL_EVENT_PARAMETER_CHANGED:
        raise ValueError(
            "Received unexpected camera control callback event, 0x%08x" % buf[0].cmd)
    mmal.mmal_buffer_header_release(buf)
camera_control_callback = mmal.MMAL_PORT_BH_CB_T(camera_control_callback)

def encoder_buffer_callback(port, buf):
    print("encoder_buffer_callback")
    mmal.mmal_buffer_header_release(buf)
    if port[0].is_enabled:
        new_buffer = ct.cast(port[0].userdata, ct.POINTER(mmal.MMAL_POOL_T))[0].queue
        if not (new_buffer and mmal.mmal_port_send_buffer(port, new_buffer) == mmal.MMAL_SUCCESS):
            raise ValueError(
                "Unable to return a buffer to the encoder port")
encoder_buffer_callback = mmal.MMAL_PORT_BH_CB_T(encoder_buffer_callback)

class PiCamera(object):
    MMAL_CAMERA_PREVIEW_PORT = 0
    MMAL_CAMERA_VIDEO_PORT = 1
    MMAL_CAMERA_CAPTURE_PORT = 2
    MMAL_CAMERA_PORTS = (
        MMAL_CAMERA_PREVIEW_PORT,
        MMAL_CAMERA_VIDEO_PORT,
        MMAL_CAMERA_CAPTURE_PORT,
        )
    VIDEO_FRAME_RATE_NUM = 30
    VIDEO_FRAME_RATE_DEN = 1
    VIDEO_OUTPUT_BUFFERS_NUM = 3
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    PREVIEW_LAYER = 2
    PREVIEW_ALPHA = 255
    PREVIEW_FRAME_RATE_NUM = 30
    PREVIEW_FRAME_RATE_DEN = 1

    DEFAULT_STILLS_RESOLUTION = (2592, 1944)
    DEFAULT_PREVIEW_RESOLUTION = (1920, 1080)

    _METER_MODES = {
        'average': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_AVERAGE,
        'spot':    mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_SPOT,
        'backlit': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_BACKLIT,
        'matrix':  mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_MATRIX,
        }
    _METER_MODES_R = {v: k for (k, v) in _METER_MODES.items()}

    _EXPOSURE_MODES = {
        'off':           mmal.MMAL_PARAM_EXPOSUREMODE_OFF,
        'auto':          mmal.MMAL_PARAM_EXPOSUREMODE_AUTO,
        'night':         mmal.MMAL_PARAM_EXPOSUREMODE_NIGHT,
        'nightpreview':  mmal.MMAL_PARAM_EXPOSUREMODE_NIGHTPREVIEW,
        'backlight':     mmal.MMAL_PARAM_EXPOSUREMODE_BACKLIGHT,
        'spotlight':     mmal.MMAL_PARAM_EXPOSUREMODE_SPOTLIGHT,
        'sports':        mmal.MMAL_PARAM_EXPOSUREMODE_SPORTS,
        'snow':          mmal.MMAL_PARAM_EXPOSUREMODE_SNOW,
        'beach':         mmal.MMAL_PARAM_EXPOSUREMODE_BEACH,
        'verylong':      mmal.MMAL_PARAM_EXPOSUREMODE_VERYLONG,
        'fixedfps':      mmal.MMAL_PARAM_EXPOSUREMODE_FIXEDFPS,
        'antishake':     mmal.MMAL_PARAM_EXPOSUREMODE_ANTISHAKE,
        'fireworks':     mmal.MMAL_PARAM_EXPOSUREMODE_FIREWORKS,
        }
    _EXPOSURE_MODES_R = {v: k for (k, v) in _EXPOSURE_MODES.items()}

    _AWB_MODES = {
        'off':           mmal.MMAL_PARAM_AWBMODE_OFF,
        'auto':          mmal.MMAL_PARAM_AWBMODE_AUTO,
        'sunlight':      mmal.MMAL_PARAM_AWBMODE_SUNLIGHT,
        'cloudy':        mmal.MMAL_PARAM_AWBMODE_CLOUDY,
        'shade':         mmal.MMAL_PARAM_AWBMODE_SHADE,
        'tungsten':      mmal.MMAL_PARAM_AWBMODE_TUNGSTEN,
        'fluorescent':   mmal.MMAL_PARAM_AWBMODE_FLUORESCENT,
        'incandescent':  mmal.MMAL_PARAM_AWBMODE_INCANDESCENT,
        'flash':         mmal.MMAL_PARAM_AWBMODE_FLASH,
        'horizon':       mmal.MMAL_PARAM_AWBMODE_HORIZON,
        }
    _AWB_MODES_R = {v: k for (k, v) in _AWB_MODES.items()}

    _IMAGE_EFFECTS = {
        'none':          mmal.MMAL_PARAM_IMAGEFX_NONE,
        'negative':      mmal.MMAL_PARAM_IMAGEFX_NEGATIVE,
        'solarize':      mmal.MMAL_PARAM_IMAGEFX_SOLARIZE,
        'posterize':     mmal.MMAL_PARAM_IMAGEFX_POSTERIZE,
        'whiteboard':    mmal.MMAL_PARAM_IMAGEFX_WHITEBOARD,
        'blackboard':    mmal.MMAL_PARAM_IMAGEFX_BLACKBOARD,
        'sketch':        mmal.MMAL_PARAM_IMAGEFX_SKETCH,
        'denoise':       mmal.MMAL_PARAM_IMAGEFX_DENOISE,
        'emboss':        mmal.MMAL_PARAM_IMAGEFX_EMBOSS,
        'oilpaint':      mmal.MMAL_PARAM_IMAGEFX_OILPAINT,
        'hatch':         mmal.MMAL_PARAM_IMAGEFX_HATCH,
        'gpen':          mmal.MMAL_PARAM_IMAGEFX_GPEN,
        'pastel':        mmal.MMAL_PARAM_IMAGEFX_PASTEL,
        'watercolour':   mmal.MMAL_PARAM_IMAGEFX_WATERCOLOUR,
        'film':          mmal.MMAL_PARAM_IMAGEFX_FILM,
        'blur':          mmal.MMAL_PARAM_IMAGEFX_BLUR,
        'saturation':    mmal.MMAL_PARAM_IMAGEFX_SATURATION,
        'colourswap':    mmal.MMAL_PARAM_IMAGEFX_COLOURSWAP,
        'washedout':     mmal.MMAL_PARAM_IMAGEFX_WASHEDOUT,
        'posterise':     mmal.MMAL_PARAM_IMAGEFX_POSTERISE,
        'colourpoint':   mmal.MMAL_PARAM_IMAGEFX_COLOURPOINT,
        'colourbalance': mmal.MMAL_PARAM_IMAGEFX_COLOURBALANCE,
        'cartoon':       mmal.MMAL_PARAM_IMAGEFX_CARTOON,
        }
    _IMAGE_EFFECTS_R = {v: k for (k, v) in _IMAGE_EFFECTS.items()}

    def __init__(self):
        bcm_host.bcm_host_init()
        self._camera = None
        self._preview = None
        self._preview_connection = None
        self._video_encoder = None
        self._video_encoder_pool = None
        self._video_encoder_connection = None
        self._image_encoder = None
        self._image_encoder_pool = None
        self._image_encoder_connection = None
        self._create_camera()

    def close(self):
        #if self._encoder and self._encoder[0].output[0][0].is_enabled:
        #    mmal.mmal_port_disable(self._encoder[0].output[0])
        #if self._video_encoder_connection:
        #    mmal.mmal_connection_destroy(self._video_encoder_connection)
        #    self._video_encoder_connection = None
        #if self._video_encoder:
        #    mmal.mmal_component_disable(self._video_encoder)
        #self._destroy_video_encoder()
        self._destroy_camera()

    def _create_camera(self):
        assert not self._camera
        self._camera = ct.POINTER(mmal.MMAL_COMPONENT_T)()
        self._check(
            mmal.mmal_component_create(
                mmal.MMAL_COMPONENT_DEFAULT_CAMERA, self._camera),
            prefix="Failed to create camera component")
        try:
            if not self._camera[0].output_num:
                raise PiCameraError("Camera doesn't have output ports")

            self._check(
                mmal.mmal_port_enable(
                    self._camera[0].control,
                    camera_control_callback),
                prefix="Unable to enable control port")

            mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                    ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                    ),
                max_stills_w=self.DEFAULT_STILLS_RESOLUTION[0],
                max_stills_h=self.DEFAULT_STILLS_RESOLUTION[1],
                stills_yuv422=0,
                one_shot_stills=0,
                max_preview_video_w=self.DEFAULT_PREVIEW_RESOLUTION[0],
                max_preview_video_h=self.DEFAULT_PREVIEW_RESOLUTION[1],
                num_preview_video_frames=3,
                stills_capture_circular_buffer_height=0,
                fast_preview_resume=0,
                use_stc_timestamp=mmal.MMAL_PARAM_TIMESTAMP_MODE_RESET_STC,
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Camera control port couldn't be configured")

            for p in self.MMAL_CAMERA_PORTS:
                port = self._camera[0].output[p]
                fmt = port[0].format
                fmt[0].encoding_variant = mmal.MMAL_ENCODING_I420
                fmt[0].encoding = mmal.MMAL_ENCODING_OPAQUE
                fmt[0].es[0].video.width = self.DEFAULT_WIDTH
                fmt[0].es[0].video.height = self.DEFAULT_HEIGHT
                fmt[0].es[0].video.crop.x = 0
                fmt[0].es[0].video.crop.y = 0
                fmt[0].es[0].video.crop.width = self.DEFAULT_WIDTH
                fmt[0].es[0].video.crop.height = self.DEFAULT_HEIGHT
                fmt[0].es[0].video.frame_rate.num = 1 if p == self.MMAL_CAMERA_CAPTURE_PORT else self.VIDEO_FRAME_RATE_NUM
                fmt[0].es[0].video.frame_rate.den = 1 if p == self.MMAL_CAMERA_CAPTURE_PORT else self.VIDEO_FRAME_RATE_DEN
                self._check(
                    mmal.mmal_port_format_commit(self._camera[0].output[p]),
                    prefix="Camera %s format couldn't be set" % {
                        self.MMAL_CAMERA_PREVIEW_PORT: "viewfinder",
                        self.MMAL_CAMERA_VIDEO_PORT:   "video",
                        self.MMAL_CAMERA_CAPTURE_PORT: "still",
                        }[p])
                if p != self.MMAL_CAMERA_PREVIEW_PORT:
                    if port[0].buffer_num < self.VIDEO_OUTPUT_BUFFERS_NUM:
                        port[0].buffer_num = self.VIDEO_OUTPUT_BUFFERS_NUM

            self._check(
                mmal.mmal_component_enable(self._camera),
                prefix="Camera component couldn't be enabled")

            self.sharpness = 0
            self.contrast = 0
            self.brightness = 50
            self.saturation = 0
            self.ISO = 400
            self.video_stabilization = False
            self.exposure_compensation = False
            self.exposure_mode = 'auto'
            self.meter_mode = 'average'
            self.awb_mode = 'auto'
            self.image_effect = 'none'
            self.color_effects = None
            self.rotation = 0
            self.hflip = self.vflip = False
            self.crop = (0.0, 0.0, 1.0, 1.0)
        except PiCameraError:
            self._destroy_camera()
            raise

    def _destroy_camera(self):
        if self._camera:
            mmal.mmal_component_disable(self._camera)
            mmal.mmal_component_destroy(self._camera)
            self._camera = None

    def _create_encoder(self):
        self._encoder = ct.POINTER(mmal.MMAL_COMPONENT_T)()
        self._check(
            mmal.mmal_component_create(
                mmal.MMAL_COMPONENT_DEFAULT_VIDEO_ENCODER, self._encoder),
            prefix="Failed to create encoder component")
        try:
            if not self._encoder[0].input_num:
                raise PiCameraError("No input ports on encoder component")
            if not self._encoder[0].output_num:
                raise PiCameraError("No output ports on encoder component")
            enc_out = self._encoder[0].output[0]
            enc_in = self._encoder[0].input[0]

            mmal.mmal_format_copy(enc_out[0].format, enc_in[0].format)
            enc_out[0].format[0].encoding = mmal.MMAL_ENCODING_H264
            enc_out[0].format[0].bitrate = 17000000
            enc_out[0].buffer_size = max(
                enc_out[0].buffer_size_recommended,
                enc_out[0].buffer_size_min)
            enc_out[0].buffer_num = max(
                enc_out[0].buffer_num_recommended,
                enc_out[0].buffer_num_min)
            self._check(
                mmal.mmal_port_format_commit(enc_out),
                prefix="Unable to set format on encoder output port")

            try:
                self._check(
                    mmal.mmal_port_parameter_set_boolean(
                        enc_in,
                        mmal.MMAL_PARAMETER_VIDEO_IMMUTABLE_INPUT,
                        1),
                    prefix="Unable to set immutable flag on encoder input port")
            except PiCameraError as e:
                print(str(e))
                # Continue rather than abort...

            self._check(
                mmal.mmal_component_enable(self._encoder),
                prefix="Unable to enable encoder component")

            self._encoder_pool = mmal.mmal_port_pool_create(
                enc_out, enc_out[0].buffer_num, enc_out[0].buffer_size)
            if not self._encoder_pool:
                raise PiCameraError(
                    "Failed to create buffer header pool for encoder component")
        except PiCameraError:
            self._destroy_encoder()
            raise

    def _destroy_encoder(self):
        if self._encoder_pool:
            mmal.mmal_port_pool_destroy(self._encoder[0].output[0], self._encoder_pool)
            self._encoder_pool = None
        if self._encoder:
            mmal.mmal_component_destroy(self._encoder)
            self._encoder = None

    def _connect_ports(self):
        self._encoder_connection = ct.POINTER(mmal.MMAL_CONNECTION_T)()
        self._check(
            mmal.mmal_connection_create(
                self._encoder_connection,
                self._camera[0].output[self.MMAL_CAMERA_VIDEO_PORT],
                self._encoder[0].input[0],
                mmal.MMAL_CONNECTION_FLAG_TUNNELLING | mmal.MMAL_CONNECTION_FLAG_ALLOCATION_ON_INPUT),
            prefix="Failed to connect camera to encoder")
        self._check(
            mmal.mmal_connection_enable(self._encoder_connection),
            prefix="Failed to enable encoder connection")
        self._encoder[0].output[0][0].userdata = ct.cast(self._encoder_pool, ct.c_void_p)
        self._check(
            mmal.mmal_port_enable(self._encoder[0].output[0][0], encoder_buffer_callback),
            prefix="Failed to setup encoder output")

    def _check(self, status, prefix=""):
        if status != mmal.MMAL_SUCCESS:
            raise PiCameraError("%s%s%s" % (prefix, ": " if prefix else "", {
                mmal.MMAL_ENOMEM:    "Out of memory",
                mmal.MMAL_ENOSPC:    "Out of resources (other than memory)",
                mmal.MMAL_EINVAL:    "Argument is invalid",
                mmal.MMAL_ENOSYS:    "Function not implemented",
                mmal.MMAL_ENOENT:    "No such file or directory",
                mmal.MMAL_ENXIO:     "No such device or address",
                mmal.MMAL_EIO:       "I/O error",
                mmal.MMAL_ESPIPE:    "Illegal seek",
                mmal.MMAL_ECORRUPT:  "Data is corrupt #FIXME not POSIX",
                mmal.MMAL_ENOTREADY: "Component is not ready #FIXME not POSIX",
                mmal.MMAL_ECONFIG:   "Component is not configured #FIXME not POSIX",
                mmal.MMAL_EISCONN:   "Port is already connected",
                mmal.MMAL_ENOTCONN:  "Port is disconnected",
                mmal.MMAL_EAGAIN:    "Resource temporarily unavailable; try again later",
                mmal.MMAL_EFAULT:    "Bad address",
                }.get(status, "Unknown status error")))

    # XXX Convert all the getters below to use mmal_port_parameter_get (if it works)

    def start_preview(self):
        if self._preview:
            raise PiCameraRuntimeError("Preview is already running")
        if not self._camera:
            raise PiCameraRuntimeError("Camera has been closed")
        self._preview = ct.POINTER(mmal.MMAL_COMPONENT_T)()
        self._check(
            mmal.mmal_component_create(
                mmal.MMAL_COMPONENT_DEFAULT_VIDEO_RENDERER, self._preview),
            prefix="Failed to create preview component")
        try:
            if not self._preview[0].input_num:
                raise PiCameraError("No input ports on preview component")

            mp = mmal.MMAL_DISPLAYREGION_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_DISPLAYREGION,
                    ct.sizeof(mmal.MMAL_DISPLAYREGION_T)
                    ),
                )
            mp.set = mmal.MMAL_DISPLAY_SET_LAYER
            mp.layer = self.PREVIEW_LAYER
            mp.set |= mmal.MMAL_DISPLAY_SET_ALPHA
            mp.alpha = self.PREVIEW_ALPHA
            mp.set |= mmal.MMAL_DISPLAY_SET_FULLSCREEN
            mp.fullscreen = 1
            self._check(
                mmal.mmal_port_parameter_set(self._preview[0].input[0], mp.hdr),
                prefix="Unable to set preview port parameters")

            self._check(
                mmal.mmal_component_enable(self._preview),
                prefix="Preview component couldn't be enabled")

            self._preview_connection = ct.POINTER(mmal.MMAL_CONNECTION_T)()
            self._check(
                mmal.mmal_connection_create(
                    self._preview_connection,
                    self._camera[0].output[self.MMAL_CAMERA_PREVIEW_PORT],
                    self._preview[0].input[0],
                    mmal.MMAL_CONNECTION_FLAG_TUNNELLING | mmal.MMAL_CONNECTION_FLAG_ALLOCATION_ON_INPUT),
                prefix="Failed to connect camera to preview")
            self._check(
                mmal.mmal_connection_enable(self._preview_connection),
                prefix="Failed to enable preview connection")

        except PiCameraError:
            self.stop_preview()
            raise

    def stop_preview(self):
        if self._preview_connection:
            mmal.mmal_connection_destroy(self._preview_connection)
            self._preview_connection = None
        if self._preview:
            mmal.mmal_component_disable(self._preview)
            mmal.mmal_component_destroy(self._preview)
            self._preview = None

    def start_recording(self, output):
        if self._video_encoder:
            raise PiCameraRuntimeError("Recording is already running")
        if not self._camera:
            raise PiCameraRuntimeError("Camera has been closed")
        # TODO

    def stop_recording(self):
        pass

    def capture(self, output):
        pass

    def _get_stills_resolution(self):
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get stills resolution")
        return (mp.max_stills_w, mp.max_stills_h)
    def _set_stills_resolution(self, value):
        try:
            w, h = value
        except (TypeError, ValueError) as e:
            raise PiCameraValueError(
                "Invalid stills resolution (width, height) tuple: %s" % value)
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get camera config")
        mp.max_stills_w = w
        mp.max_stills_h = h
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
            prefix="Failed to set stills resolution")
    stills_resolution = property(_get_stills_resolution, _set_stills_resolution)

    def _get_still_frames(self):
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get still frames setting")
        return mp.one_shot_stills == 1
    def _set_still_frames(self, value):
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get camera config")
        mp.one_shot_stills = [0, 1][bool(value)]
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
            prefix="Failed to set still frames setting")
    still_frames = property(_get_still_frames, _set_still_frames)

    def _get_preview_resolution(self):
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get preview resolution")
        return (mp.max_preview_video_w, mp.max_preview_video_h)
    def _set_preview_resolution(self, value):
        try:
            w, h = value
        except (TypeError, ValueError) as e:
            raise PiCameraValueError(
                "Invalid preview resolution (width, height) tuple: %s" % value)
        mp = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get camera config")
        mp.max_preview_video_w = w
        mp.max_preview_video_h = h
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
            prefix="Failed to set preview resolution")
    preview_resolution = property(_get_preview_resolution, _set_preview_resolution)

    def _get_saturation(self):
        mp = mmal.MMAL_RATIONAL_T()
        self._check(
            mmal.mmal_port_parameter_get_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_SATURATION,
                mp
                ),
            prefix="Failed to get saturation")
        return mp.num
    def _set_saturation(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid saturation value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid saturation value: %s" % value)
        self._check(
            mmal.mmal_port_parameter_set_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_SATURATION,
                mmal.MMAL_RATIONAL_T(value, 100)
                ),
            prefix="Failed to set saturation")
    saturation = property(_get_saturation, _set_saturation)

    def _get_sharpness(self):
        mp = mmal.MMAL_RATIONAL_T()
        self._check(
            mmal.mmal_port_parameter_get_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_SHARPNESS,
                mp
                ),
            prefix="Failed to get sharpness")
        return mp.num
    def _set_sharpness(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid sharpness value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid sharpness value: %s" % value)
        self._check(
            mmal.mmal_port_parameter_set_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_SHARPNESS,
                mmal.MMAL_RATIONAL_T(value, 100)
                ),
            prefix="Failed to set sharpness")
    sharpness = property(_get_sharpness, _set_sharpness)

    def _get_contrast(self):
        mp = mmal.MMAL_RATIONAL_T()
        self._check(
            mmal.mmal_port_parameter_get_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_CONTRAST,
                mp
                ),
            prefix="Failed to get contrast")
        return mp.num
    def _set_contrast(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid contrast value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid contrast value: %s" % value)
        self._check(
            mmal.mmal_port_parameter_set_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_CONTRAST,
                mmal.MMAL_RATIONAL_T(value, 100)
                ),
            prefix="Failed to set contrast")
    contrast = property(_get_contrast, _set_contrast)

    def _get_brightness(self):
        mp = mmal.MMAL_RATIONAL_T()
        self._check(
            mmal.mmal_port_parameter_get_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_BRIGHTNESS,
                mp
                ),
            prefix="Failed to get brightness")
        return mp.num
    def _set_brightness(self, value):
        try:
            if not (0 <= value <= 100):
                raise PiCameraValueError("Invalid brightness value: %d (valid range 0..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid brightness value: %s" % value)
        self._check(
            mmal.mmal_port_parameter_set_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_BRIGHTNESS,
                mmal.MMAL_RATIONAL_T(value, 100)
                ),
            prefix="Failed to set brightness")
    brightness = property(_get_brightness, _set_brightness)

    def _get_ISO(self):
        mp = mmal.MMAL_RATIONAL_T()
        self._check(
            mmal.mmal_port_parameter_get_rational(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_ISO,
                mp
                ),
            prefix="Failed to get ISO")
        return mp.num
    def _set_ISO(self, value):
        # XXX Valid values?
        self._check(
            mmal.mmal_port_parameter_set_uint32(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_ISO,
                value
                ),
            prefix="Failed to set ISO")
    ISO = property(_get_ISO, _set_ISO)

    def _get_meter_mode(self):
        mp = mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_EXP_METERING_MODE,
                ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get meter mode")
        return self._METER_MODES_R[mp.value]
    def _set_meter_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXP_METERING_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T)
                    ),
                self._METER_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set meter mode")
        except KeyError:
            raise PiCameraValueError("Invalid metering mode: %s" % value)
    meter_mode = property(_get_meter_mode, _set_meter_mode)

    def _get_video_stabilization(self):
        mp = mmal.MMAL_BOOL_T()
        self._check(
            mmal.mmal_port_parameter_get_boolean(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_VIDEO_STABILISATION,
                mp
                ),
            prefix="Failed to get video stabilization")
        return mp == mmal.MMAL_TRUE
    def _set_video_stabilization(self, value):
        try:
            self._check(
                mmal.mmal_port_parameter_set_boolean(
                    self._camera[0].control,
                    mmal.MMAL_PARAMETER_VIDEO_STABILISATION,
                    {
                        False: mmal.MMAL_FALSE,
                        True:  mmal.MMAL_TRUE,
                        }[value]
                    ),
                prefix="Failed to set video stabilization")
        except KeyError:
            raise PiCameraValueError("Invalid video stabilization boolean value: %s" % value)
    video_stabilization = property(_get_video_stabilization, _set_video_stabilization)

    def _get_exposure_compensation(self):
        mp = mmal.MMAL_BOOL_T()
        self._check(
            mmal.mmal_port_parameter_get_boolean(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_EXPOSURE_COMP,
                mp
                ),
            prefix="Failed to get exposure compensation")
        return mp == mmal.MMAL_TRUE
    def _set_exposure_compensation(self, value):
        try:
            self._check(
                mmal.mmal_port_parameter_set_boolean(
                    self._camera[0].control,
                    mmal.MMAL_PARAMETER_EXPOSURE_COMP,
                    {
                        False: mmal.MMAL_FALSE,
                        True:  mmal.MMAL_TRUE,
                        }[value]
                    ),
                prefix="Failed to set exposure compensation")
        except KeyError:
            raise PiCameraValueError("Invalid exposure compensation boolean value: %s" % value)
    exposure_compensation = property(_get_exposure_compensation, _set_exposure_compensation)

    def _get_exposure_mode(self):
        mp = mmal.MMAL_PARAMETER_EXPOSUREMODE_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_EXPOSURE_MODE,
                ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMODE_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get exposure mode")
        return self._EXPOSURE_MODES_R[mp.value]
    def _set_exposure_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXPOSURE_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMODE_T)
                    ),
                self._EXPOSURE_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set exposure mode")
        except KeyError:
            raise PiCameraValueError("Invalid exposure mode: %s" % value)
    exposure_mode = property(_get_exposure_mode, _set_exposure_mode)

    def _get_awb_mode(self):
        mp = mmal.MMAL_PARAMETER_AWBMODE_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_AWB_MODE,
                ct.sizeof(mmal.MMAL_PARAMETER_AWBMODE_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get auto-white-balance mode")
        return self._AWB_MODES_R[mp.value]
    def _set_awb_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_AWBMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_AWB_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_AWBMODE_T)
                    ),
                self._AWB_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set auto-white-balance mode")
        except KeyError:
            raise PiCameraValueError("Invalid auto-white-balance mode: %s" % value)
    awb_mode = property(_get_awb_mode, _set_awb_mode)

    def _get_image_effect(self):
        mp = mmal.MMAL_PARAMETER_IMAGEFX_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_IMAGE_EFFECT,
                ct.sizeof(mmal.MMAL_PARAMETER_IMAGEFX_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get image effect")
        return self._IMAGE_EFFECTS_R[mp.value]
    def _set_image_effect(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_IMAGEFX_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_IMAGE_EFFECT,
                    ct.sizeof(mmal.MMAL_PARAMETER_IMAGEFX_T)
                    ),
                self._IMAGE_EFFECTS[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set image effect")
        except KeyError:
            raise PiCameraValueError("Invalid image effect: %s" % value)
    image_effect = property(_get_image_effect, _set_image_effect)

    def _get_color_effects(self):
        mp = mmal.MMAL_PARAMETER_COLOURFX_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_COLOUR_EFFECT,
                ct.sizeof(mmal.MMAL_PARAMETER_COLOURFX_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get color effects")
        if mp.enable == mmal.MMAL_TRUE:
            return (mp.u, mp.v)
        else:
            return None
    def _set_color_effects(self, value):
        if value is None:
            enable = mmal.MMAL_FALSE
            u = v = 128
        else:
            enable = mmal.MMAL_TRUE
            try:
                u, v = value
            except (TypeError, ValueError) as e:
                raise PiCameraValueError(
                    "Invalid color effect (u, v) tuple: %s" % value)
        mp = mmal.MMAL_PARAMETER_COLOURFX_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_COLOUR_EFFECT,
                ct.sizeof(mmal.MMAL_PARAMETER_COLOURFX_T)
                ),
            enable, u, v
            )
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
            prefix="Failed to set color effects")
    color_effects = property(_get_color_effects, _set_color_effects)

    def _get_rotation(self):
        mp = ct.c_int32()
        self._check(
            mmal.mmal_port_parameter_get_int32(
                self._camera[0].output[0],
                mmal.MMAL_PARAMETER_ROTATION,
                mp
                ),
            prefix="Failed to get rotation")
        return int(mp)
    def _set_rotation(self, value):
        try:
            value = ((int(value) % 360) // 90) * 90
        except ValueError:
            raise PiCameraValueError("Invalid rotation angle: %s" % value)
        for p in self.MMAL_CAMERA_PORTS:
            self._check(
                mmal.mmal_port_parameter_set_int32(
                    self._camera[0].output[p],
                    mmal.MMAL_PARAMETER_ROTATION,
                    value
                    ),
                prefix="Failed to set rotation")
    rotation = property(_get_rotation, _set_rotation)

    def _get_vflip(self):
        mp = mmal.MMAL_PARAMETER_MIRROR_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_MIRROR,
                ct.sizeof(mmal.MMAL_PARAMETER_MIRROR_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].output[0], mp.hdr),
            prefix="Failed to get vertical flip")
        return mp.value in (mmal.MMAL_PARAM_MIRROR_VERTICAL, mmal.MMAL_PARAM_MIRROR_BOTH)
    def _set_vflip(self, value):
        value = bool(value)
        for p in self.MMAL_CAMERA_PORTS:
            mp = mmal.MMAL_PARAMETER_MIRROR_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_MIRROR,
                    ct.sizeof(mmal.MMAL_PARAMETER_MIRROR_T)
                    ),
                {
                    (False, False): mmal.MMAL_PARAM_MIRROR_NONE,
                    (True,  False): mmal.MMAL_PARAM_MIRROR_VERTICAL,
                    (False, True):  mmal.MMAL_PARAM_MIRROR_HORIZONTAL,
                    (True,  True):  mmal.MMAL_PARAM_MIRROR_BOTH,
                    }[(value, self.hflip)]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].output[p], mp.hdr),
                prefix="Failed to set vertical flip")
    vflip = property(_get_vflip, _set_vflip)

    def _get_hflip(self):
        mp = mmal.MMAL_PARAMETER_MIRROR_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_MIRROR,
                ct.sizeof(mmal.MMAL_PARAMETER_MIRROR_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].output[0], mp.hdr),
            prefix="Failed to get horizontal flip")
        return mp.value in (mmal.MMAL_PARAM_MIRROR_HORIZONTAL, mmal.MMAL_PARAM_MIRROR_BOTH)
    def _set_hflip(self, value):
        value = bool(value)
        for p in self.MMAL_CAMERA_PORTS:
            mp = mmal.MMAL_PARAMETER_MIRROR_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_MIRROR,
                    ct.sizeof(mmal.MMAL_PARAMETER_MIRROR_T)
                    ),
                {
                    (False, False): mmal.MMAL_PARAM_MIRROR_NONE,
                    (True,  False): mmal.MMAL_PARAM_MIRROR_VERTICAL,
                    (False, True):  mmal.MMAL_PARAM_MIRROR_HORIZONTAL,
                    (True,  True):  mmal.MMAL_PARAM_MIRROR_BOTH,
                    }[(self.vflip, value)]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].output[p], mp.hdr),
                prefix="Failed to set horizontal flip")
    hflip = property(_get_hflip, _set_hflip)

    def _get_crop(self):
        mp = mmal.MMAL_PARAMETER_INPUT_CROP_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_INPUT_CROP,
                ct.sizeof(mmal.MMAL_PARAMETER_INPUT_CROP_T)
                ))
        self._check(
            mmal.mmal_port_parameter_get(self._camera[0].control, mp.hdr),
            prefix="Failed to get crop")
        return (
            mp[0].rect.x / 65535.0,
            mp[0].rect.y / 65535.0,
            mp[0].rect.width / 65535.0,
            mp[0].rect.height / 65535.0,
            )
    def _set_crop(self, value):
        try:
            x, y, w, h = value
        except (TypeError, ValueError) as e:
            raise PiCameraValueError("Invalid crop rectangle (x, y, w, h) tuple: %s" % value)
        mp = mmal.MMAL_PARAMETER_INPUT_CROP_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_INPUT_CROP,
                ct.sizeof(mmal.MMAL_PARAMETER_INPUT_CROP_T)
                ),
            mmal.MMAL_RECT_T(
                int(65535 * x),
                int(65535 * y),
                int(65535 * w),
                int(65535 * h)
                ),
            )
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
            prefix="Failed to set crop")
    crop = property(_get_crop, _set_crop)


if __name__ == '__main__':
    camera = PiCamera()
    try:
        camera.open()
        while True:
            time.sleep(0.1)
    finally:
        camera.close()
