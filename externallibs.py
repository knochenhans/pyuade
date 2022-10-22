from ctypes import *
from ctypes_classes import *

libc = CDLL("/usr/lib/libc.so.6")

libc.free.argtypes = [c_void_p]

CDLL("/usr/lib/libbencodetools.so", mode=RTLD_GLOBAL)
# libuade = CDLL("/usr/lib/libuade.so", mode=RTLD_GLOBAL)
libuade = CDLL("/tmp/uade/src/frontends/libuade/libuade.so", mode=RTLD_GLOBAL)

libuade.uade_new_state.argtypes = [c_void_p]
libuade.uade_new_state.restype = c_void_p

libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
libuade.uade_read_file.restype = c_void_p

libuade.uade_get_sampling_rate.argtypes = [c_void_p]

libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]

libuade.uade_get_song_info.argtypes = [c_void_p]
libuade.uade_get_song_info.restype = POINTER(uade_song_info)

libuade.uade_read_notification.argtypes = [
    POINTER(uade_notification), c_void_p]

libuade.uade_cleanup_notification.argtypes = [POINTER(uade_notification)]

libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_read.restype = c_ssize_t

libuade.uade_stop.argtypes = [c_void_p]

libuade.uade_cleanup_state.argtypes = [c_void_p]

libuade.uade_next_subsong.argtypes = [c_void_p]

libuade.uade_get_time_position.argtypes = [c_int, c_void_p]
libuade.uade_get_time_position.restype = c_double

libuade.uade_is_rmc_file.argtypes = [c_void_p]

libuade.uade_file_ext_to_format_version.argtypes = [c_void_p]
libuade.uade_file_ext_to_format_version.restype = POINTER(
    uade_ext_to_format_version)

libuade.uade_seek.argtypes = [c_int, c_double, c_int, c_void_p]

libuade.uade_is_seeking.argtypes = [c_void_p]

libuade.uade_get_event.argtypes = [c_void_p, c_void_p]

libuade.uade_get_fd.argtypes = [c_void_p]

libuade.uade_event_name.argtypes = [c_void_p]
libuade.uade_event_name.restype = c_char_p
