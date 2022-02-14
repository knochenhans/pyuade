from ctypes import *

PATH_MAX = 4096
UADE_MAX_MESSAGE_SIZE = 8 + 4096


class uade_path(Structure):
    pass


uade_path._fields_ = [
    ("name", c_char * PATH_MAX),
]


class uade_ep_options(Structure):
    pass


uade_ep_options._fields_ = [
    ("o", c_char * 256),
    ("s", c_size_t)
]


class uade_ao_options(Structure):
    pass


uade_ao_options._fields_ = [
    ("o", c_char * 256)
]


class uade_subsong_info(Structure):
    pass


uade_subsong_info._fields_ = [
    ("cur", c_int),
    ("min", c_int),
    ("def", c_int),
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
    pass


eagleplayer._fields_ = [
    ("playername", c_char_p),
    ("nextensions", c_size_t),
    ("extensions", POINTER(c_char_p)),
    ("flags", c_int),
    ("attributelist", POINTER(uade_attribute)),
]


class uade_detection_info(Structure):
    pass


UADE_MAX_EXT_LEN = 16

uade_detection_info._fields_ = [
    ("custom", c_int),
    ("content", c_int),

    ("ext", c_char * UADE_MAX_EXT_LEN),
    ("ep", POINTER(eagleplayer)),
]


class uade_song_info(Structure):
    pass


uade_song_info._fields_ = [
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


class uade_notification_song_end(Structure):
    pass


uade_notification_song_end._fields_ = [
    ("happy", c_int),
    ("stopnow", c_int),
    ("subsong", c_int),
    ("happy", c_int64),
    ("reason", c_void_p),
]


class uade_notification_union(Union):
    pass


uade_notification_union._fields_ = [
    ("msg", c_char_p),
    ("song_end", uade_notification_song_end),
]


class uade_notification(Structure):
    pass


uade_notification._fields_ = [
    ("type", c_int),
    ("uade_notification_union", uade_notification_union),
]


class ao_sample_format(Structure):
    pass


ao_sample_format._fields_ = [
    ("bits", c_int),
    ("rate", c_int),
    ("channels", c_int),
    ("byte_format", c_int),
    ("matrix", c_char_p),
]


class ao_device(Structure):
    pass


ao_device._fields_ = [
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
