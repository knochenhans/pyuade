from ctypes import (
    Structure,
    POINTER,
    c_char,
    c_char_p,
    c_int,
    c_size_t,
    c_double,
    c_uint32,
    c_uint64,
    c_ubyte,
    c_int64,
    Union,
    c_float,
    c_void_p,
)
from enum import IntEnum

UADE_CHANNELS = 2
UADE_BYTES_PER_SAMPLE = 2
UADE_BYTES_PER_FRAME = UADE_CHANNELS * UADE_BYTES_PER_SAMPLE

PATH_MAX = 4096
UADE_MAX_MESSAGE_SIZE = 8 + 4096


class uade_path(Structure):
    _fields_ = [
        ("name", c_char * PATH_MAX),
    ]


class uade_ep_options(Structure):
    _fields_ = [("o", c_char * 256), ("s", c_size_t)]


class uade_ao_options(Structure):
    _fields_ = [("o", c_char * 256)]


class uade_subsong_info(Structure):
    _fields_ = [
        ("cur", c_int),
        ("min", c_int),
        ("def_", c_int),
        ("max", c_int),
    ]


class uade_attribute(Structure):
    pass


uade_attribute._fields_ = [
    ("next", POINTER(uade_attribute)),
    ("flag", c_int),
    ("s", c_char_p),
    ("i", c_int),
    ("d", c_double),
]


class eagleplayer(Structure):
    _fields_ = [
        ("playername", c_char_p),
        ("nextensions", c_size_t),
        ("extensions", POINTER(c_char_p)),
        ("flags", c_int),
        ("attributelist", POINTER(uade_attribute)),
    ]


UADE_MAX_EXT_LEN = 16


class uade_ext_to_format_version(Structure):
    _fields_ = [
        ("file_ext", c_char_p),
        ("format", c_char_p),
        ("version", c_char_p),
    ]


class uade_detection_info(Structure):
    _fields_ = [
        ("custom", c_int),
        ("content", c_int),
        ("ext", c_char * UADE_MAX_EXT_LEN),
        ("ep", POINTER(eagleplayer)),
    ]


class uade_song_info(Structure):
    _fields_ = [
        ("subsongs", uade_subsong_info),
        ("detectioninfo", uade_detection_info),
        ("modulebytes", c_size_t),
        ("modulemd5", c_char * 33),
        ("duration", c_double),
        ("subsongbytes", c_uint64),
        ("songbytes", c_uint64),
        ("modulefname", c_char * PATH_MAX),
        ("playerfname", c_char * PATH_MAX),
        ("formatname", c_char * 256),
        ("modulename", c_char * 256),
        ("playername", c_char * 256),
    ]


class UADE_NOTIFICATION_TYPE(IntEnum):
    UADE_NOTIFICATION_MESSAGE = 0
    UADE_NOTIFICATION_SONG_END = 1


class uade_notification_song_end(Structure):
    _fields_ = [
        ("happy", c_int),
        ("stopnow", c_int),
        ("subsong", c_int),
        ("subsongbytes", c_int64),
        ("reason", c_char_p),
    ]


class uade_notification_union(Union):
    _fields_ = [
        ("msg", c_char_p),
        ("song_end", uade_notification_song_end),
    ]


class uade_notification(Structure):
    _fields_ = [
        ("type", c_int),
        ("uade_notification_union", uade_notification_union),
    ]


class UADE_SEEK_MODE(IntEnum):
    UADE_SEEK_NOT_SEEKING = 0
    UADE_SEEK_SONG_RELATIVE = 1
    UADE_SEEK_SUBSONG_RELATIVE = 2
    UADE_SEEK_POSITION_RELATIVE = 3


class UADE_EVENT_TYPE(IntEnum):
    UADE_EVENT_INVALID = 0
    UADE_EVENT_DATA = 1
    UADE_EVENT_EAGAIN = 2
    UADE_EVENT_FORMAT_NAME = 3
    UADE_EVENT_MESSAGE = 4
    UADE_EVENT_MODULE_NAME = 5
    UADE_EVENT_PLAYER_NAME = 6
    UADE_EVENT_READY = 7
    UADE_EVENT_REQUEST_AMIGA_FILE = 8
    UADE_EVENT_SONG_END = 9
    UADE_EVENT_SUBSONG_INFO = 10


class uade_event_data(Structure):
    _fields_ = [
        ("size", c_size_t),
        ("data", c_ubyte * UADE_MAX_MESSAGE_SIZE),
    ]


class uade_event_songend(Structure):
    _fields_ = [
        ("happy", c_int),
        ("stopnow", c_int),
        ("tailbytes", c_int),
        ("reason", c_char * 256),
    ]


class uade_event_union(Union):
    _fields_ = [
        ("data", uade_event_data),
        ("msg", c_char * 1024),
        ("songend", uade_event_songend),
        ("subsongs", uade_subsong_info),
    ]


class uade_event(Structure):
    _fields_ = [
        ("type", c_int),
        ("uade_event_union", uade_event_union),
    ]


class uade_dir(Structure):
    _fields_ = [
        ("name", c_char * PATH_MAX),
    ]


class uade_config(Structure):
    _fields_ = [
        ("action_keys", c_char),
        ("ao_options", c_char_p),
        ("ao_options_set", c_char),
        ("basedir", uade_dir),
        ("basedir_set", c_char),
        ("buffer_time", c_int),
        ("content_detection", c_char),
        ("cygwin_drive_workaround", c_char),
        ("ep_options", c_char_p),
        ("ep_options_set", c_char),
        ("filter_type", c_char),
        ("frequency", c_int),
        ("led_forced", c_char),
        ("led_state", c_char),
        ("gain_enable", c_char),
        ("gain", c_float),
        ("headphones", c_char),
        ("headphones2", c_char),
        ("ignore_player_check", c_char),
        ("resampler", c_char_p),
        ("resampler_set", c_char),
        ("no_ep_end", c_char),
        ("no_filter", c_char),
        ("no_postprocessing", c_char),
        ("normalise", c_char),
        ("normalise_parameter", c_char_p),
        ("one_subsong", c_char),
        ("panning", c_float),
        ("panning_enable", c_char),
        ("random_play", c_char),
        ("recursive_mode", c_char),
        ("silence_timeout", c_int),
        ("song_title", c_char_p),
        ("song_title_set", c_char),
        ("speed_hack", c_char),
        ("subsong_timeout", c_int),
        ("timeout", c_int),
        ("use_text_scope", c_char),
        ("use_timeouts", c_char),
        ("use_ntsc", c_char),
        ("use_quad_mode", c_char),  # Added by Airmann
        ("verbose", c_char),
    ]


class uade_song(Structure):
    _fields_ = [
        ("md5", c_char * 33),
        ("module_filename", c_char * PATH_MAX),
        ("playername", c_char * 256),
        ("modulename", c_char * 256),
        ("formatname", c_char * 256),
        ("buf", POINTER(c_ubyte)),
        ("bufsize", c_size_t),
        ("min_subsong", c_int),
        ("max_subsong", c_int),
        ("cur_subsong", c_int),
        ("playtime", c_int),
        ("flags", c_int),
        ("nsubsongs", c_int),
        ("subsongs", POINTER(c_ubyte)),
        ("songattributes", POINTER(uade_attribute)),
        ("ep_options", uade_ep_options),
        ("normalisation", c_char_p),
        ("out_bytes", c_int64),
        ("silence_count", c_int64),
    ]


class uade_effect_t(IntEnum):
    UADE_EFFECT_ALLOW = 0
    UADE_EFFECT_GAIN = 1
    UADE_EFFECT_HEADPHONES = 2
    UADE_EFFECT_HEADPHONES2 = 3
    UADE_EFFECT_PAN = 4
    UADE_EFFECT_NORMALISE = 5


class uade_effect(Structure):
    _fields_ = [
        ("enabled", c_int),  # uade_effect_t
        ("gain", c_int),
        ("pan", c_int),
        ("rate", c_int),
    ]


class eagleplayermap(Structure):
    _fields_ = [
        ("extension", c_char_p),
        ("player", POINTER(eagleplayer)),
    ]


# IPC


class uade_msgtype(IntEnum):
    UADE_MSG_FIRST = 0
    UADE_COMMAND_ACTIVATE_DEBUGGER = 1
    UADE_COMMAND_CHANGE_SUBSONG = 2
    UADE_COMMAND_CONFIG = 3
    UADE_COMMAND_SCORE = 4
    UADE_COMMAND_PLAYER = 5
    UADE_COMMAND_MODULE = 6
    UADE_COMMAND_READ = 7
    UADE_COMMAND_REBOOT = 8
    UADE_COMMAND_SET_SUBSONG = 9
    UADE_COMMAND_IGNORE_CHECK = 10
    UADE_COMMAND_SONG_END_NOT_POSSIBLE = 11
    UADE_COMMAND_SET_NTSC = 12
    UADE_COMMAND_FILTER = 13
    UADE_COMMAND_SET_FREQUENCY = 14
    UADE_COMMAND_SET_PLAYER_OPTION = 15
    UADE_COMMAND_SET_QUAD_MODE = 16  # by Airmann
    UADE_COMMAND_SET_RESAMPLING_MODE = 17
    UADE_COMMAND_SPEED_HACK = 18
    UADE_COMMAND_TOKEN = 19
    UADE_COMMAND_USE_TEXT_SCOPE = 20
    UADE_REPLY_MSG = 21
    UADE_REPLY_CANT_PLAY = 22
    UADE_REPLY_CAN_PLAY = 23
    UADE_REPLY_SONG_END = 24
    UADE_REPLY_SUBSONG_INFO = 25
    UADE_REPLY_PLAYERNAME = 26
    UADE_REPLY_MODULENAME = 27
    UADE_REPLY_FORMATNAME = 28
    UADE_REPLY_DATA = 29
    UADE_MSG_LAST = 30


class uade_msg(Structure):
    _fields_ = [
        ("msgtype", c_uint32),
        ("size", c_uint32),
        ("data", c_ubyte * 0),
    ]
    _pack_ = 1


class eagleplayerstore(Structure):
    _fields_ = [
        ("nplayers", c_size_t),
        ("players", POINTER(eagleplayer)),
        ("nextensions", c_size_t),
        ("map", POINTER(eagleplayermap)),
    ]


class uade_control_state(IntEnum):
    UADE_INITIAL_STATE = 0
    UADE_R_STATE = 1
    UADE_S_STATE = 2


class uade_ipc(Structure):
    _fields_ = [
        ("input", c_void_p),
        ("output", c_void_p),
        ("inputbytes", c_uint64),
        ("inputbuffer", c_char * UADE_MAX_MESSAGE_SIZE),
        ("state", c_int),  # uade_control_state
    ]


class uade_state(Structure):
    _fields_ = [
        ("config", uade_config),
        ("song", POINTER(uade_song)),
        ("effects", uade_effect),
        ("ep", POINTER(eagleplayer)),
        ("validconfig", c_int),
        ("playerstore", POINTER(eagleplayerstore)),
        ("ipc", uade_ipc),
        ("pid", c_int),  # pid_t is typically an int in C
    ]
