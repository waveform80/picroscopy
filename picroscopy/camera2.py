#!/usr/bin/env python

import time
import ctypes as ct

import picroscopy.mmal as mmal
import picroscopy.bcm_host as bcm_host


class PiCameraError(Exception):
    """
    Base class for PiCamera errors
    """

class PiCameraValueError(PiCameraError, ValueError):
    """
    Raised when an invalid value is fed to a PiCamera object
    """



def camera_control_callback(port, buf):
    if buf[0].cmd != mmal.MMAL_EVENT_PARAMETER_CHANGED:
        raise ValueError(
            "Received unexpected camera control callback event, 0x%08x" % buf[0].cmd)
    mmal.mmal_buffer_header_release(buf)
camera_control_callback = mmal.MMAL_PORT_BH_CB_T(camera_control_callback)

def encoder_buffer_callback(port, buf):
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
    PREVIEW_OPACITY = 255
    PREVIEW_FRAME_RATE_NUM = 30
    PREVIWE_FRAME_RATE_DEN = 1

    def __init__(self):
        bcm_host.bcm_host_init()
        self._camera = None
        self._preview = None
        self._preview_connection = None
        self._encoder = None
        self._encoder_pool = None
        self._encoder_connection = None
        self._create_camera()
        self._create_preview()
        self._create_encoder()
        self._connect_ports()

    def close(self):
        if self._camera and self._camera[0].output[self.MMAL_CAMERA_CAPTURE_PORT][0].is_enabled:
            mmal.mmal_port_disable(self._camera[0].output[self.MMAL_CAMERA_CAPTURE_PORT])
        if self._encoder and self._encoder[0].output[0][0].is_enabled:
            mmal.mmal_port_disable(self._encoder[0].output[0])
        if self._preview_connection:
            mmal.mmal_connection_destroy(self._preview_connection)
        if self._encoder_connection:
            mmal.mmal_connection_destroy(self._encoder_connection)
        if self._encoder:
            mmal.mmal_component_disable(self._encoder)
        if self._preview:
            mmal.mmal_component_disable(self._preview)
        if self._camera:
            mmal.mmal_component_disable(self._camera)
        self._destroy_encoder()
        self._destroy_preview()
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
                max_stills_w=self.DEFAULT_WIDTH,
                max_stills_h=self.DEFAULT_HEIGHT,
                stills_yuv422=0,
                one_shot_stills=0,
                max_preview_video_w=self.DEFAULT_WIDTH,
                max_preview_video_h=self.DEFAULT_HEIGHT,
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

            # XXX Remove this line when getters are modified
            self._hflip = self._vflip = False
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
            mmal.mmal_component_destroy(self._camera)
            self._camera = None

    def _create_preview(self):
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
            mp.alpha = self.PREVIEW_OPACITY
            mp.set |= mmal.MMAL_DISPLAY_SET_FULLSCREEN
            mp.fullscreen = 1
            self._check(
                mmal.mmal_port_parameter_set(self._preview[0].input[0], mp.hdr),
                prefix="Unable to set preview port parameters")

            self._check(
                mmal.mmal_component_enable(self._preview),
                prefix="Preview component couldn't be enabled")
        except PiCameraError:
            self._destroy_preview()
            raise

    def _destroy_preview(self):
        if self._preview:
            mmal.mmal_component_destroy(self._preview)
            self._preview = None

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

            self._check(
                mmal.mmal_port_parameter_set_boolean(
                    enc_in,
                    mmal.MMAL_PARAMETER_VIDEO_IMMUTABLE_INPUT,
                    1),
                prefix="Unable to set immutable flag on encoder input port")

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
        self._preview_connection = ct.POINTER(mmal.MMAL_CONNECTION_T)()
        self._check(
            mmal.mmal_connection_create(
                self._preview_connection,
                self._camera[0].output[self.MMAL_CAMERA_PREVIEW_PORT],
                self._preview[0].input[0],
                mmal.MMAL_CONNECTION_FLAG_TUNNELLING | mmal.MMAL_CONNECTION_FLAG_ALLOCATION_ON_INPUT),
            prefix="Failed to connect camera to preview")
        self._encoder_connection = ct.POINTER(mmal.MMAL_CONNECTION_T)()
        self._check(
            mmal.mmal_connection_create(
                self._encoder_connection,
                self._camera[0].output[self.MMAL_CAMERA_VIDEO_PORT],
                self._encoder[0].input[0],
                mmal.MMAL_CONNECTION_FLAG_TUNNELLING | mmal.MMAL_CONNECTION_FLAG_ALLOCATION_ON_INPUT),
            prefix="Failed to connect camera to encoder")
        self._encoder[0].output[0][0].userdata = self._encoder_pool
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

    def _get_saturation(self):
        return self._saturation
    def _set_saturation(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid saturation value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid saturation value: %s" % value)
        self._check(mmal.mmal_port_parameter_set_rational(
            self._camera[0].control,
            mmal.MMAL_PARAMETER_SATURATION,
            mmal.MMAL_RATIONAL_T(value, 100)
            ),
            prefix="Failed to set saturation")
        self._saturation = value
    saturation = property(_get_saturation, _set_saturation)

    def _get_sharpness(self):
        return self._sharpness
    def _set_sharpness(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid sharpness value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid sharpness value: %s" % value)
        self._check(mmal.mmal_port_parameter_set_rational(
            self._camera[0].control,
            mmal.MMAL_PARAMETER_SHARPNESS,
            mmal.MMAL_RATIONAL_T(value, 100)
            ),
            prefix="Failed to set sharpness")
        self._sharpness = value
    sharpness = property(_get_sharpness, _set_sharpness)

    def _get_contrast(self):
        return self._contrast
    def _set_contrast(self, value):
        try:
            if not (-100 <= value <= 100):
                raise PiCameraValueError("Invalid contrast value: %d (valid range -100..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid contrast value: %s" % value)
        self._check(mmal.mmal_port_parameter_set_rational(
            self._camera[0].control,
            mmal.MMAL_PARAMETER_CONTRAST,
            mmal.MMAL_RATIONAL_T(value, 100)
            ),
            prefix="Failed to set contrast")
        self._contrast = value
    contrast = property(_get_contrast, _set_contrast)

    def _get_brightness(self):
        return self._brightness
    def _set_brightness(self, value):
        try:
            if not (0 <= value <= 100):
                raise PiCameraValueError("Invalid brightness value: %d (valid range 0..100)" % value)
        except TypeError:
            raise PiCameraValueError("Invalid brightness value: %s" % value)
        self._check(mmal.mmal_port_parameter_set_rational(
            self._camera[0].control,
            mmal.MMAL_PARAMETER_BRIGHTNESS,
            mmal.MMAL_RATIONAL_T(value, 100)
            ),
            prefix="Failed to set brightness")
        self._brightness = value
    brightness = property(_get_brightness, _set_brightness)

    def _get_ISO(self):
        return self._ISO
    def _set_ISO(self, value):
        # XXX Valid values?
        self._check(mmal.mmal_port_parameter_set_uint32(
            self._camera[0].control,
            mmal.MMAL_PARAMETER_ISO,
            value
            ),
            prefix="Failed to set ISO")
        self._ISO = value
    ISO = property(_get_ISO, _set_ISO)

    def _get_meter_mode(self):
        return self._meter_mode
    def _set_meter_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXP_METERING_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMETERINGMODE_T)
                    ),
                {
                    'average': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_AVERAGE,
                    'spot':    mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_SPOT,
                    'backlit': mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_BACKLIT,
                    'matrix':  mmal.MMAL_PARAM_EXPOSUREMETERINGMODE_MATRIX,
                    }[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set meter mode")
            self._meter_mode = value
        except KeyError:
            raise PiCameraValueError("Invalid metering mode: %s" % value)
    meter_mode = property(_get_meter_mode, _set_meter_mode)

    def _get_video_stabilization(self):
        return self._video_stabilization
    def _set_video_stabilization(self, value):
        try:
            self._check(mmal.mmal_port_parameter_set_boolean(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_VIDEO_STABILISATION,
                {
                    False: mmal.MMAL_FALSE,
                    True:  mmal.MMAL_TRUE,
                    }[value]
                ),
                prefix="Failed to set video stabilization")
            self._video_stabilization = value
        except KeyError:
            raise PiCameraValueError("Invalid video stabilization boolean value: %s" % value)
    video_stabilization = property(_get_video_stabilization, _set_video_stabilization)

    def _get_exposure_compensation(self):
        return self._exposure_compensation
    def _set_exposure_compensation(self, value):
        try:
            self._check(mmal.mmal_port_parameter_set_boolean(
                self._camera[0].control,
                mmal.MMAL_PARAMETER_EXPOSURE_COMP,
                {
                    False: mmal.MMAL_FALSE,
                    True:  mmal.MMAL_TRUE,
                    }[value]
                ),
                prefix="Failed to set exposure compensation")
            self._exposure_compensation = value
        except KeyError:
            raise PiCameraValueError("Invalid exposure compensation boolean value: %s" % value)
    exposure_compensation = property(_get_exposure_compensation, _set_exposure_compensation)

    def _get_exposure_mode(self):
        return self._exposure_mode
    def _set_exposure_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_EXPOSUREMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_EXPOSURE_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_EXPOSUREMODE_T)
                    ),
                {
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
                    }[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set exposure mode")
            self._exposure_mode = value
        except KeyError:
            raise PiCameraValueError("Invalid exposure mode: %s" % value)
    exposure_mode = property(_get_exposure_mode, _set_exposure_mode)

    def _get_awb_mode(self):
        return self._awb_mode
    def _set_awb_mode(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_AWBMODE_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_AWB_MODE,
                    ct.sizeof(mmal.MMAL_PARAMETER_AWBMODE_T)
                    ),
                {
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
                    }[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set auto-white-balance mode")
            self._awb_mode = value
        except KeyError:
            raise PiCameraValueError("Invalid auto-white-balance mode: %s" % value)
    awb_mode = property(_get_awb_mode, _set_awb_mode)

    def _get_image_effect(self):
        return self._image_effect
    def _set_image_effect(self, value):
        try:
            mp = mmal.MMAL_PARAMETER_IMAGEFX_T(
                mmal.MMAL_PARAMETER_HEADER_T(
                    mmal.MMAL_PARAMETER_IMAGE_EFFECT,
                    ct.sizeof(mmal.MMAL_PARAMETER_IMAGEFX_T)
                    ),
                {
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
                    }[value]
                )
            self._check(
                mmal.mmal_port_parameter_set(self._camera[0].control, mp.hdr),
                prefix="Failed to set image effect")
            self._image_effect = value
        except KeyError:
            raise PiCameraValueError("Invalid image effect: %s" % value)
    image_effect = property(_get_image_effect, _set_image_effect)

    def _get_color_effects(self):
        return self._color_effects
    def _set_color_effects(self, value):
        if value is None:
            enable = mmal.MMAL_FALSE
            u = v = 128
        else:
            enable = mmal.MMAL_TRUE
            try:
                u, v = value
            except (TypeError, ValueError) as e:
                raise PiCameraValueError("Invalid color effect (u, v) tuple: %s" % value)
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
        self._color_effects = value
    color_effects = property(_get_color_effects, _set_color_effects)

    def _get_rotation(self):
        return self._rotation
    def _set_rotation(self, value):
        try:
            value = ((int(value) % 360) // 90) * 90
        except ValueError:
            raise PiCameraValueError("Invalid rotation angle: %s" % value)
        for p in self.MMAL_CAMERA_PORTS:
            self._check(mmal.mmal_port_parameter_set_int32(
                self._camera[0].output[p],
                mmal.MMAL_PARAMETER_ROTATION,
                value
                ),
                prefix="Failed to set rotation")
        self._rotation = value
    rotation = property(_get_rotation, _set_rotation)

    def _get_vflip(self):
        return self._vflip
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
        self._vflip = value
    vflip = property(_get_vflip, _set_vflip)

    def _get_hflip(self):
        return self._hflip
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
        self._hflip = value
    hflip = property(_get_hflip, _set_hflip)

    def _get_crop(self):
        return self._crop
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
        self._crop = value
    crop = property(_get_crop, _set_crop)


if __name__ == '__main__':
    camera = PiCamera()
    try:
        while True:
            time.sleep(500)
    finally:
        camera.close()
