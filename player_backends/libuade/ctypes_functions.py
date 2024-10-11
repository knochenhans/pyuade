from ctypes import (
    CDLL,
    CFUNCTYPE,
    RTLD_GLOBAL,
    c_int16,
    c_void_p,
    c_size_t,
    c_char_p,
    c_ssize_t,
    POINTER,
    c_uint,
)
import sys
from ctypes.util import find_library

from player_backends.libuade.ctypes_classes import *

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
libuade.uade_cleanup_state.restype = None

# File I/O
libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
libuade.uade_read_file.restype = c_void_p

libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_read.restype = c_ssize_t

libuade.uade_get_fd.argtypes = [c_void_p]
libuade.uade_get_fd.restype = c_int

# Playback control
libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]
libuade.uade_play.restype = c_int

libuade.uade_play_from_buffer.argtypes = [c_char_p, c_void_p, c_size_t, c_int, c_void_p]
libuade.uade_play_from_buffer.restype = c_int

libuade.uade_stop.argtypes = [c_void_p]
libuade.uade_stop.restype = c_int

libuade.uade_seek.argtypes = [c_int, c_double, c_int, c_void_p]
libuade.uade_seek.restype = c_int

libuade.uade_seek_samples.argtypes = [c_int, c_ssize_t, c_int, c_void_p]
libuade.uade_seek_samples.restype = c_int

libuade.uade_next_subsong.argtypes = [c_void_p]
libuade.uade_next_subsong.restype = c_int

# Information retrieval
libuade.uade_get_song_info.argtypes = [c_void_p]
libuade.uade_get_song_info.restype = POINTER(uade_song_info)

libuade.uade_get_time_position.argtypes = [c_int, c_void_p]
libuade.uade_get_time_position.restype = c_double

libuade.uade_is_rmc_file.argtypes = [c_char_p]
libuade.uade_is_rmc_file.restype = c_int

libuade.uade_file_ext_to_format_version.argtypes = [c_void_p]
libuade.uade_file_ext_to_format_version.restype = POINTER(uade_ext_to_format_version)

libuade.uade_get_sampling_rate.argtypes = [c_void_p]
libuade.uade_get_sampling_rate.restype = c_int

# Notification handling
libuade.uade_read_notification.argtypes = [POINTER(uade_notification), c_void_p]
libuade.uade_read_notification.restype = c_int

libuade.uade_cleanup_notification.argtypes = [POINTER(uade_notification)]
libuade.uade_cleanup_notification.restype = None

# Miscellaneous
libuade.uade_is_seeking.argtypes = [c_void_p]
libuade.uade_is_seeking.restype = c_int

libuade.uade_get_event.argtypes = [c_void_p, c_void_p]
libuade.uade_get_event.restype = c_int

libuade.uade_event_name.argtypes = [c_void_p]
libuade.uade_event_name.restype = c_char_p

libuade.uade_song_info.argtypes = [c_char_p, c_uint, c_char_p, c_int]
libuade.uade_song_info.restype = c_int

libuade.uade_new_config.argtypes = []
libuade.uade_new_config.restype = c_void_p

libuade.uade_set_debug.argtypes = [c_void_p]
libuade.uade_set_debug.restype = None

libuade.uade_enable_uadecore_log_collection.argtypes = [c_void_p]
libuade.uade_enable_uadecore_log_collection.restype = None

# IPC
libuade.uade_check_fix_string.argtypes = [c_void_p, c_size_t]

libuade.uade_parse_u32_message.argtypes = [POINTER(c_uint), c_void_p]
libuade.uade_parse_u32_message.restype = c_int

libuade.uade_parse_two_u32s_message.argtypes = [
    POINTER(c_uint),
    POINTER(c_uint),
    c_void_p,
]
libuade.uade_parse_two_u32s_message.restype = c_int

libuade.uade_receive_message.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_receive_message.restype = c_int

libuade.uade_receive_short_message.argtypes = [c_int, c_void_p]
libuade.uade_receive_short_message.restype = c_int

libuade.uade_receive_string.argtypes = [c_char_p, c_int, c_size_t, c_void_p]
libuade.uade_receive_string.restype = c_int

libuade.uade_send_message.argtypes = [c_void_p, c_void_p]
libuade.uade_send_message.restype = c_int

libuade.uade_send_short_message.argtypes = [c_int, c_void_p]
libuade.uade_send_short_message.restype = c_int

libuade.uade_send_string.argtypes = [c_int, c_char_p, c_void_p]
libuade.uade_send_string.restype = c_int

libuade.uade_send_u32.argtypes = [c_int, c_uint, c_void_p]
libuade.uade_send_u32.restype = c_int

libuade.uade_send_two_u32s.argtypes = [c_int, c_uint, c_uint, c_void_p]
libuade.uade_send_two_u32s.restype = c_int

libuade.uade_set_peer.argtypes = [c_void_p, c_int, c_char_p, c_char_p]

libuade.uade_add_playtime.argtypes = [c_void_p, c_char_p, c_uint]
libuade.uade_add_playtime.restype = c_void_p

libuade.uade_free_song_db.argtypes = [c_void_p]
libuade.uade_free_song_db.restype = None

libuade.uade_lookup_song.argtypes = [c_void_p, c_void_p]
libuade.uade_lookup_song.restype = None

libuade.uade_read_content_db.argtypes = [c_char_p, c_void_p]
libuade.uade_read_content_db.restype = c_int

libuade.uade_read_song_conf.argtypes = [c_char_p, c_void_p]
libuade.uade_read_song_conf.restype = c_int

libuade.uade_save_content_db.argtypes = [c_char_p, c_void_p]
libuade.uade_save_content_db.restype = None

libuade.uade_test_silence.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_test_silence.restype = c_int

libuade.uade_update_song_conf.argtypes = [c_char_p, c_char_p, c_char_p]
libuade.uade_update_song_conf.restype = c_int

libuade.uade_analyze_eagleplayer.argtypes = [
    c_void_p,
    c_void_p,
    c_size_t,
    c_char_p,
    c_size_t,
    c_void_p,
]
libuade.uade_analyze_eagleplayer.restype = c_int

libuade.uade_free_playerstore.argtypes = [c_void_p]
libuade.uade_free_playerstore.restype = None

libuade.uade_set_config_options_from_flags.argtypes = [c_void_p, c_int]
libuade.uade_set_config_options_from_flags.restype = c_int

libuade.uade_parse_attribute_from_string.argtypes = [
    c_void_p,
    c_void_p,
    c_char_p,
    c_size_t,
]
libuade.uade_parse_attribute_from_string.restype = c_int

libuade.uade_dirname.argtypes = [c_char_p, c_char_p, c_size_t]
libuade.uade_dirname.restype = c_char_p

libuade.uade_find_amiga_file.argtypes = [c_char_p, c_size_t, c_char_p, c_char_p]
libuade.uade_find_amiga_file.restype = c_int

libuade.uade_arch_kill_and_wait_uadecore.argtypes = [POINTER(uade_ipc), POINTER(c_int)]
libuade.uade_arch_kill_and_wait_uadecore.restype = None

libuade.uade_arch_spawn.argtypes = [
    POINTER(uade_ipc),
    POINTER(c_int),
    c_char_p,
    POINTER(c_int),
]
libuade.uade_arch_spawn.restype = c_int

libuade.uade_filesize.argtypes = [POINTER(c_size_t), c_char_p]
libuade.uade_filesize.restype = c_int

libuade.uade_config_set_defaults.argtypes = [c_void_p]
libuade.uade_config_set_defaults.restype = None

libuade.uade_config_set_option.argtypes = [c_void_p, c_int, c_char_p]
libuade.uade_config_set_option.restype = None

libuade.uade_config_toggle_boolean.argtypes = [c_void_p, c_int]
libuade.uade_config_toggle_boolean.restype = c_int

libuade.uade_effect_disable.argtypes = [c_void_p, c_int]
libuade.uade_effect_disable.restype = None

libuade.uade_effect_disable_all.argtypes = [c_void_p]
libuade.uade_effect_disable_all.restype = None

libuade.uade_effect_enable.argtypes = [c_void_p, c_int]
libuade.uade_effect_enable.restype = None

libuade.uade_effect_is_enabled.argtypes = [c_void_p, c_int]
libuade.uade_effect_is_enabled.restype = c_int

libuade.uade_effect_toggle.argtypes = [c_void_p, c_int]
libuade.uade_effect_toggle.restype = None

libuade.uade_effect_gain_set_amount.argtypes = [c_void_p, c_float]
libuade.uade_effect_gain_set_amount.restype = None

libuade.uade_effect_pan_set_amount.argtypes = [c_void_p, c_float]
libuade.uade_effect_pan_set_amount.restype = None

libuade.uade_effect_set_defaults.argtypes = [POINTER(uade_state)]
libuade.uade_effect_set_defaults.restype = None

libuade.uade_effect_set_sample_rate.argtypes = [POINTER(uade_state), c_int]
libuade.uade_effect_set_sample_rate.restype = None

libuade.uade_effect_run.argtypes = [POINTER(uade_state), POINTER(c_int16), c_int]
libuade.uade_effect_run.restype = None

libuade.uade_is_our_file.argtypes = [c_char_p, c_void_p]
libuade.uade_is_our_file.restype = c_int

libuade.uade_is_our_file_from_buffer.argtypes = [c_char_p, c_void_p, c_size_t, c_void_p]
libuade.uade_is_our_file_from_buffer.restype = c_int

libuade.uade_is_rmc.argtypes = [c_char_p, c_size_t]
libuade.uade_is_rmc.restype = c_int

libuade.uade_is_verbose.argtypes = [c_void_p]
libuade.uade_is_verbose.restype = c_int

libuade.uade_get_rmc_from_state.argtypes = [c_void_p]
libuade.uade_get_rmc_from_state.restype = c_void_p

libuade.uade_load_amiga_file.argtypes = [c_char_p, c_char_p, c_void_p]
libuade.uade_load_amiga_file.restype = c_void_p

libuade.uade_set_filter_state.argtypes = [c_void_p, c_int]
libuade.uade_set_filter_state.restype = c_int

libuade.uade_set_amiga_loader.argtypes = [
    CFUNCTYPE(c_void_p, c_char_p, c_char_p, c_void_p, c_void_p),
    c_void_p,
    c_void_p,
]
libuade.uade_set_amiga_loader.restype = None

libuade.uade_set_song_options.argtypes = [c_char_p, c_char_p, c_void_p]
libuade.uade_set_song_options.restype = c_int

libuade.uade_rmc_get_file.argtypes = [c_void_p, c_char_p]
libuade.uade_rmc_get_file.restype = c_void_p

libuade.uade_rmc_get_module.argtypes = [POINTER(c_void_p), c_void_p]
libuade.uade_rmc_get_module.restype = c_int

libuade.uade_rmc_get_meta.argtypes = [c_void_p]
libuade.uade_rmc_get_meta.restype = c_void_p

libuade.uade_rmc_get_subsongs.argtypes = [c_void_p]
libuade.uade_rmc_get_subsongs.restype = c_void_p

libuade.uade_rmc_get_song_length.argtypes = [c_void_p]
libuade.uade_rmc_get_song_length.restype = c_double

libuade.uade_rmc_decode.argtypes = [c_void_p, c_size_t]
libuade.uade_rmc_decode.restype = c_void_p

libuade.uade_rmc_decode_file.argtypes = [c_char_p]
libuade.uade_rmc_decode_file.restype = c_void_p

libuade.uade_rmc_record_file.argtypes = [c_void_p, c_char_p, c_void_p, c_size_t]
libuade.uade_rmc_record_file.restype = c_int

libuade.uade_atomic_fread.argtypes = [c_void_p, c_size_t, c_size_t, c_void_p]
libuade.uade_atomic_fread.restype = c_size_t

libuade.uade_atomic_fwrite.argtypes = [c_void_p, c_size_t, c_size_t, c_void_p]
libuade.uade_atomic_fwrite.restype = c_size_t

libuade.uade_file.argtypes = [c_char_p, c_void_p, c_size_t]
libuade.uade_file.restype = c_void_p

libuade.uade_empty_file.argtypes = [c_char_p]
libuade.uade_empty_file.restype = c_void_p

libuade.uade_file_free.argtypes = [c_void_p]
libuade.uade_file_free.restype = None

libuade.uade_file_load.argtypes = [c_char_p]
libuade.uade_file_load.restype = c_void_p

libuade.uade_filemagic.argtypes = [POINTER(c_ubyte), c_size_t, c_char_p, c_size_t, c_char_p, c_int]
libuade.uade_filemagic.restype = None

# List of further exported functions
# uade_atomic_close
# uade_atomic_dup2
# uade_atomic_read
# uade_atomic_write
# uade_convert_to_double
# uade_free_playerstore
# uade_get_two_ws_separated_fields
# uade_ipc_prepare_two_u32s
# uade_load_config
# uade_load_initial_config
# uade_load_initial_song_conf
# uade_MD5Final
# uade_MD5Init
# uade_MD5Update
# uade_merge_configs
# uade_open_create_home
# uade_parse_subsongs
# uade_prepare_filter_command
# uade_read_and_split_lines
# uade_read_request
# uade_receive_file
# uade_request_amiga_file
# uade_send_file
# uade_send_filter_command
# uade_set_effects
# uade_set_options_from_ep_attributes
# uade_set_options_from_song_attributes
# uade_skip_and_terminate_word
# uade_song_initialization
# uade_subsong_control
# uade_walk_directories
# uade_xbasename
# uade_xfgets
