from ctypes import *
from enum import IntEnum

from xcffib import Struct

PATH_MAX = 4096
UADE_MAX_MESSAGE_SIZE = 8 + 4096


class uade_path(Structure):
    _fields_ = [
        ("name", c_char * PATH_MAX),
    ]


class uade_ep_options(Structure):
    _fields_ = [
        ("o", c_char * 256),
        ("s", c_size_t)
    ]


class uade_ao_options(Structure):
    _fields_ = [
        ("o", c_char * 256)
    ]


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
    UADE_SEEK_NOT_SEEKING = 0,
    UADE_SEEK_SONG_RELATIVE = 1,
    UADE_SEEK_SUBSONG_RELATIVE = 2,
    UADE_SEEK_POSITION_RELATIVE = 3,


class UADE_EVENT_TYPE(IntEnum):
    UADE_EVENT_INVALID = 0,
    UADE_EVENT_DATA = 1,
    UADE_EVENT_EAGAIN = 2,
    UADE_EVENT_FORMAT_NAME = 3,
    UADE_EVENT_MESSAGE = 4,
    UADE_EVENT_MODULE_NAME = 5,
    UADE_EVENT_PLAYER_NAME = 6,
    UADE_EVENT_READY = 7,
    UADE_EVENT_REQUEST_AMIGA_FILE = 8,
    UADE_EVENT_SONG_END = 9,
    UADE_EVENT_SUBSONG_INFO = 10,


class uade_event_data(Structure):
    _fields_ = [
        ("size", c_size_t),
        ("data", c_uint8 * UADE_MAX_MESSAGE_SIZE),
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
        ("subsongs", uade_subsong_info)
    ]


class uade_event(Structure):
    _fields_ = [
        ("type", c_int),
        ("union", uade_event_union)
    ]


# libao

class ao_sample_format(Structure):
    _fields_ = [
        ("bits", c_int),
        ("rate", c_int),
        ("channels", c_int),
        ("byte_format", c_int),
        ("matrix", c_char_p),
    ]


class ao_device(Structure):
    _fields_ = [
        ("type", c_int),
        ("driver_id", c_int),
        ("funcs", c_void_p),
        ("file", c_void_p),
        ("client_byte_format", c_int),
        ("machine_byte_format", c_int),
        ("driver_byte_format", c_int),
        ("swap_buffer", c_char_p),
        ("swap_buffer_size", c_int),
        ("internal", c_void_p),
    ]
