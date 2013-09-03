"""
Some rudimentary EXIF handling, specifically handling those tags that are used
by raspistill.
"""

CAMERA_MAKE   = 271
CAMERA_MODEL  = 272
SOFTWARE      = 305
ARTIST        = 315
COPYRIGHT     = 33432
F_NUMBER      = 33437
ISO           = 34855
EXPOSURE_TIME = 33434
FOCAL_LENGTH  = 37386

EXPOSURE_MODE = 41986
EXPOSURE_MODES = {
    0: 'Auto',
    1: 'Manual',
    2: 'Auto-bracket',
    }

EXPOSURE_PROGRAM = 34850
EXPOSURE_PROGRAMS = {
    0: 'Undefined',
    1: 'Manual',
    2: 'Normal',
    3: 'Aperture priority',
    4: 'Shutter priority',
    5: 'Creative program',
    6: 'Action program',
    7: 'Portrait mode',
    8: 'Landscape mode',
    }

WHITE_BALANCE = 41987
WHITE_BALANCES = {
    0: 'Auto',
    1: 'Manual',
    }

METERING_MODE = 37383
METERING_MODES = {
    0:   'Unknown',
    1:   'Average',
    2:   'Center weighted average',
    3:   'Spot',
    4:   'Multi-spot',
    5:   'Pattern',
    6:   'Partial',
    255: 'Other',
    }

TAG_NAMES = {
    ARTIST:           'Artist',
    COPYRIGHT:        'Copyright',
    SOFTWARE:         'Software',
    CAMERA_MAKE:      'Camera Make',
    CAMERA_MODEL:     'Camera Model',
    F_NUMBER:         'F-Number',
    EXPOSURE_MODE:    'Exposure Mode',
    EXPOSURE_PROGRAM: 'Exposure Program',
    EXPOSURE_TIME:    'Exposure Time',
    METERING_MODE:    'Metering Mode',
    WHITE_BALANCE:    'White Balance',
    ISO:              'ISO',
    FOCAL_LENGTH:     'Focal Length',
    }

TAG_VALUES = {
    ARTIST:           lambda v: v,
    COPYRIGHT:        lambda v: v,
    SOFTWARE:         lambda v: v,
    CAMERA_MAKE:      lambda v: v,
    CAMERA_MODEL:     lambda v: v,
    F_NUMBER:         lambda v: '%.1f' % (v[0]/v[1]),
    EXPOSURE_MODE:    lambda v: EXPOSURE_MODES.get(v, 'Unknown'),
    EXPOSURE_PROGRAM: lambda v: EXPOSURE_PROGRAMS.get(v, 'Unknown'),
    EXPOSURE_TIME:    lambda v: '1/%ds' % (0.5 + v[1]/v[0]),
    METERING_MODE:    lambda v: METERING_MODES.get(v, 'Unknown'),
    WHITE_BALANCE:    lambda v: WHITE_BALANCES.get(v, 'Unknown'),
    ISO:              lambda v: str(v),
    FOCAL_LENGTH:     lambda v: '%.1fmm' % (v[0]/v[1]),
    }

def format_exif(data):
    """
    Formats EXIF data for user display.

    Only certain tags will be included in the output; tags not used by the
    RPI's raspistill application are excluded as are those tags which
    raspistill simply fills with invalid values.
    """
    if not data:
        return {}
    return {
        TAG_NAMES[key]: TAG_VALUES[key](value)
        for (key, value) in data.items()
        if key in TAG_NAMES
        }
