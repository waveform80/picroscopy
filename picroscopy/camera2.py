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

__all__ = [
    'PiCameraError',
    'PiCameraRuntimeError',
    'PiCameraValueError',
    'PiCamera',
    ]


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
    DEFAULT_STILL_RESOLUTION = (2592, 1944)
    DEFAULT_VIDEO_RESOLUTION = (1920, 1080)
    DEFAULT_FRAME_RATE_NUM = 30
    DEFAULT_FRAME_RATE_DEN = 1
    FULL_FRAME_RATE_NUM = 15
    FULL_FRAME_RATE_DEN = 1
    VIDEO_OUTPUT_BUFFERS_NUM = 3
    PREVIEW_LAYER = 2
    PREVIEW_ALPHA = 255

    METER_MODES = {
        'average': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_AVERAGE,
        'spot':    mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_SPOT,
        'backlit': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_BACKLIT,
        'matrix':  mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_MATRIX,
        }

    EXPOSURE_MODES = {
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

    AWB_MODES = {
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

    IMAGE_EFFECTS = {
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

    _METER_MODES_R    = {v: k for (k, v) in METER_MODES.items()}
    _EXPOSURE_MODES_R = {v: k for (k, v) in EXPOSURE_MODES.items()}
    _AWB_MODES_R      = {v: k for (k, v) in AWB_MODES.items()}
    _IMAGE_EFFECTS_R  = {v: k for (k, v) in IMAGE_EFFECTS.items()}

    def __init__(self):
        self._camera = None
        self._camera_config = mmal.MMAL_PARAMETER_CAMERA_CONFIG_T(
            mmal.MMAL_PARAMETER_HEADER_T(
                mmal.MMAL_PARAMETER_CAMERA_CONFIG,
                ct.sizeof(mmal.MMAL_PARAMETER_CAMERA_CONFIG_T)
                ))
        self._preview = None
        self._preview_connection = None
        self._video_encoder = None
        self._video_encoder_pool = None
        self._video_encoder_connection = None
        self._image_encoder = None
        self._image_encoder_pool = None
        self._image_encoder_connection = None
        self._create_camera()

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

            cc = self._camera_config
            cc.max_stills_w=self.DEFAULT_STILL_RESOLUTION[0]
            cc.max_stills_h=self.DEFAULT_STILL_RESOLUTION[1]
            cc.stills_yuv422=0
            cc.one_shot_stills=0
            cc.max_preview_video_w=self.DEFAULT_VIDEO_RESOLUTION[0]
            cc.max_preview_video_h=self.DEFAULT_VIDEO_RESOLUTION[1]
            cc.num_preview_video_frames=3
            cc.stills_capture_circular_buffer_height=0
            cc.fast_preview_resume=0
            cc.use_stc_timestamp=mmal.MMAL_PARAM_TIMESTAMP_MODE_RESET_STC
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, cc.hdr),
                prefix="Camera control port couldn't be configured")

            for p in self.MMAL_CAMERA_PORTS:
                port = self._camera[0].output[p]
                fmt = port[0].format
                fmt[0].encoding_variant = mmal.MMAL_ENCODING_I420
                fmt[0].encoding = mmal.MMAL_ENCODING_OPAQUE
                fmt[0].es[0].video.width = cc.max_preview_video_w
                fmt[0].es[0].video.height = cc.max_preview_video_h
                fmt[0].es[0].video.crop.x = 0
                fmt[0].es[0].video.crop.y = 0
                fmt[0].es[0].video.crop.width = cc.max_preview_video_w
                fmt[0].es[0].video.crop.height = cc.max_preview_video_h
                fmt[0].es[0].video.frame_rate.num = 1 if p == self.MMAL_CAMERA_CAPTURE_PORT else self.DEFAULT_FRAME_RATE_NUM
                fmt[0].es[0].video.frame_rate.den = 1 if p == self.MMAL_CAMERA_CAPTURE_PORT else self.DEFAULT_FRAME_RATE_DEN
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

    def _check_camera_open(self):
        if self.closed:
            raise PiCameraRuntimeError("Camera is closed")

    def _check_preview_stopped(self):
        if self.previewing:
            raise PiCameraRuntimeError("Preview is currently running")

    def _check_recording_stopped(self):
        if self.recording:
            raise PiCameraRuntimeError("Recording is currently running")

    def close(self):
        """
        Finalizes the state of the camera.

        After successfully constructing a :class:`PiCamera` object, you should
        ensure you call the :meth:`close` method once you are finished with the
        camera (e.g. in the ``finally`` section of a ``try..finally`` block).
        This method stops all recording and preview activities and releases all
        resources associated with the camera; this is necessary to prevent GPU
        memory leaks.
        """
        #if self._encoder and self._encoder[0].output[0][0].is_enabled:
        #    mmal.mmal_port_disable(self._encoder[0].output[0])
        #if self._video_encoder_connection:
        #    mmal.mmal_connection_destroy(self._video_encoder_connection)
        #    self._video_encoder_connection = None
        #if self._video_encoder:
        #    mmal.mmal_component_disable(self._video_encoder)
        #self._destroy_video_encoder()
        if self.recording:
            self.stop_recording()
        if self.previewing:
            self.stop_preview()
        self._destroy_camera()

    def start_preview(self):
        """
        Starts a preview session over the current display.

        This method starts a new preview running at the configured resolution
        (see :prop:`preview_resolution`). Most camera properties can be
        modified "live" while the preview is running (e.g. :prop:`brightness`).
        The preview typically overrides whatever is currently visible on the
        display. To stop the preview and reveal the display again, call
        :meth:`stop_preview`. The preview can be started and stopped multiple
        times during the lifetime of the :class:`PiCamera` object.
        """
        self._check_camera_open()
        self._check_preview_stopped()
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
        """
        Stops the preview session and shuts down the preview window display.

        If :meth:`start_preview` has previously been called, this method shuts
        down the preview display which generally results in the underlying TTY
        becoming visible again. If a preview is not currently running, no
        exception is raised - the method will simply do nothing.
        """
        if self._preview_connection:
            mmal.mmal_connection_destroy(self._preview_connection)
            self._preview_connection = None
        if self._preview:
            mmal.mmal_component_disable(self._preview)
            mmal.mmal_component_destroy(self._preview)
            self._preview = None

    def start_recording(self, output):
        """
        Start recording video from the camera, storing it as an H264 stream.

        If ``output`` is a string, it will be treated as a filename for a new
        file which the H264 stream will be written to. Otherwise, ``output`` is
        assumed to be a file-like object and the H264 data is appended to it
        (the implementation only assumes the object has a ``write()`` method -
        no other methods will be called).
        """
        self._check_camera_open()
        self._check_recording_stopped()
        # TODO

    def stop_recording(self):
        # TODO
        pass

    def capture(self, output):
        """
        Capture an image from the camera, storing it as a JPEG in output.

        If ``output`` is a string, it will be treated as a filename for a new
        file which the JPEG data will be written to. Otherwise, ``output`` is
        assumed to a be a file-like object and the JPEG data is appended to it
        (the implementation only assumes the object has a ``write()`` method -
        no other methods will be called).
        """
        # TODO
        pass

    @property
    def closed(self):
        """
        Returns True if the :meth:`close` method has been called.
        """
        return not self._camera

    @property
    def recording(self):
        """
        Returns True if the :meth:`start_recording` method has been called,
        and no :meth:`stop_recording` call has been made yet.
        """
        # XXX Should probably check this is actually enabled...
        return bool(self._video_encoder)

    @property
    def previewing(self):
        """
        Returns True if the :meth:`start_preview` method has been called,
        and no :meth:`stop_preview` call has been made yet.
        """
        # XXX Should probably check this is actually enabled...
        return bool(self._preview)

    def _get_stills_resolution(self):
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
        return (self._camera_config.max_preview_video_w, self._camera_config.max_preview_video_h)
    def _set_preview_resolution(self, value):
        self._check_camera_open()
        self._check_preview_stopped()
        self._check_recording_stopped()
        try:
            w, h = value
        except (TypeError, ValueError) as e:
            raise PiCameraValueError(
                "Invalid preview resolution (width, height) tuple: %s" % value)
        self._check(
            mmal.mmal_component_disable(self._camera),
            prefix="Failed to disable camera")
        self._camera_config.max_preview_video_w = w
        self._camera_config.max_preview_video_h = h
        self._check(
            mmal.mmal_port_parameter_set(self._camera[0].control, self._camera_config.hdr),
            prefix="Failed to set preview resolution")
        fmt = self._camera[0].output[self.MMAL_CAMERA_PREVIEW_PORT][0].format[0].es[0]
        fmt.video.width = w
        fmt.video.height = h
        fmt.video.crop.x = 0
        fmt.video.crop.y = 0
        fmt.video.crop.width = w
        fmt.video.crop.height = h
        # At resolutions higher than 1080p, drop the frame rate (GPU can only
        # manage 15fps at full frame)
        if (w > self.DEFAULT_VIDEO_RESOLUTION[0]) or (h > self.DEFAULT_VIDEO_RESOLUTION[1]):
            fmt.video.frame_rate.num = self.FULL_FRAME_RATE_NUM
            fmt.video.frame_rate.den = self.FULL_FRAME_RATE_DEN
        else:
            fmt.video.frame_rate.num = self.DEFAULT_FRAME_RATE_NUM
            fmt.video.frame_rate.den = self.DEFAULT_FRAME_RATE_DEN
        self._check(
            mmal.mmal_port_format_commit(self._camera[0].output[self.MMAL_CAMERA_PREVIEW_PORT]),
            prefix="Camera preview format couldn't be set")
        self._check(
            mmal.mmal_component_enable(self._camera),
            prefix="Failed to enable camera")
    preview_resolution = property(_get_preview_resolution, _set_preview_resolution)

    def _get_saturation(self):
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXP_METERING_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T)
                    ),
                self.METER_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set meter mode")
        except KeyError:
            raise PiCameraValueError("Invalid metering mode: %s" % value)
    meter_mode = property(_get_meter_mode, _set_meter_mode)

    def _get_video_stabilization(self):
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXPOSURE_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMODE_T)
                    ),
                self.EXPOSURE_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set exposure mode")
        except KeyError:
            raise PiCameraValueError("Invalid exposure mode: %s" % value)
    exposure_mode = property(_get_exposure_mode, _set_exposure_mode)

    def _get_awb_mode(self):
        self._check_camera_open()
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
        self._check_camera_open()
        try:
            mp = mmal.MMAL_PARAMETER_AWBMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_AWB_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_AWBMODE_T)
                    ),
                self.AWB_MODES[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set auto-white-balance mode")
        except KeyError:
            raise PiCameraValueError("Invalid auto-white-balance mode: %s" % value)
    awb_mode = property(_get_awb_mode, _set_awb_mode)

    def _get_image_effect(self):
        self._check_camera_open()
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
        self._check_camera_open()
        try:
            mp = mmal.MMAL_PARAMETER_IMAGEFX_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_IMAGE_EFFECT,
                    ct.sizeof(mmal.MMAL_PARAMETER_IMAGEFX_T)
                    ),
                self.IMAGE_EFFECTS[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set image effect")
        except KeyError:
            raise PiCameraValueError("Invalid image effect: %s" % value)
    image_effect = property(_get_image_effect, _set_image_effect)

    def _get_color_effects(self):
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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
        self._check_camera_open()
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


bcm_host.bcm_host_init()

