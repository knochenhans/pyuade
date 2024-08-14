from ctypes import (
    CDLL,
    RTLD_GLOBAL,
    c_void_p,
    c_size_t,
    c_char_p,
    c_ssize_t,
    POINTER,
    c_uint,
)
import sys
from ctypes.util import find_library

from ctypes_classes import *

bencode_path = find_library("bencodetools")
if not bencode_path:
    sys.exit("Error: bencodetools not found")

try:
    CDLL(bencode_path, mode=RTLD_GLOBAL)
except OSError as e:
    sys.exit(f"Error loading bencodetools: {e}")

uade_path_ = find_library("uade")
if not uade_path_:
    sys.exit("Error: uade not found")

try:
    libuade = CDLL(uade_path_, mode=RTLD_GLOBAL)
except OSError as e:
    sys.exit(f"Error loading uade: {e}")


# State management
libuade.uade_new_state.argtypes = [c_void_p]
libuade.uade_new_state.restype = c_void_p

libuade.uade_cleanup_state.argtypes = [c_void_p]

# File I/O
libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
libuade.uade_read_file.restype = c_void_p

libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_read.restype = c_ssize_t

libuade.uade_get_fd.argtypes = [c_void_p]
libuade.uade_get_fd.restype = c_int

# Playback control
libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]
libuade.uade_play_from_buffer.argtypes = [c_char_p, c_void_p, c_size_t, c_int, c_void_p]
libuade.uade_stop.argtypes = [c_void_p]

libuade.uade_seek.argtypes = [c_int, c_double, c_int, c_void_p]
libuade.uade_seek_samples.argtypes = [c_int, c_int, c_int, c_void_p]

libuade.uade_next_subsong.argtypes = [c_void_p]

# Information retrieval
libuade.uade_get_song_info.argtypes = [c_void_p]
libuade.uade_get_song_info.restype = POINTER(uade_song_info)

libuade.uade_get_time_position.argtypes = [c_int, c_void_p]
libuade.uade_get_time_position.restype = c_double

libuade.uade_is_rmc_file.argtypes = [c_void_p]

libuade.uade_file_ext_to_format_version.argtypes = [c_void_p]
libuade.uade_file_ext_to_format_version.restype = POINTER(uade_ext_to_format_version)
libuade.uade_get_sampling_rate.argtypes = [c_void_p]

# Notification handling
libuade.uade_read_notification.argtypes = [POINTER(uade_notification), c_void_p]
libuade.uade_cleanup_notification.argtypes = [POINTER(uade_notification)]

# Miscellaneous
libuade.uade_is_seeking.argtypes = [c_void_p]
libuade.uade_get_event.argtypes = [c_void_p, c_void_p]
libuade.uade_event_name.argtypes = [c_void_p]
libuade.uade_event_name.restype = c_char_p

libuade.uade_song_info.argtypes = [c_char_p, c_uint, c_char_p, c_int]

libuade.uade_new_config.argtypes = []
libuade.uade_new_config.restype = c_void_p

libuade.uade_set_debug.argtypes = [c_void_p]

libuade.uade_enable_uadecore_log_collection.argtypes = [c_void_p]