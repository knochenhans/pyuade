import ctypes
from ctypes import (
    c_uint32,
    c_int32,
    c_int64,
    c_float,
    c_int16,
    c_void_p,
    c_double,
    c_char_p,
    c_uint8,
    c_int,
    c_size_t,
    c_uint64,
    Structure,
    POINTER,
)
from ctypes.util import find_library

libopenmpt_path = find_library("openmpt")
if not libopenmpt_path:
    raise OSError("libopenmpt library not found")
LIBOPENMPT = ctypes.cdll.LoadLibrary(libopenmpt_path)

LIBOPENMPT_STREAM_CALLBACKS_BUFFER = None
LIBOPENMPT_STREAM_CALLBACKS_FD = None
LIBOPENMPT_STREAM_CALLBACKS_FILE = None
OPENMPT_ERROR_BASE = 256
OPENMPT_ERROR_ARGUMENT_NULL_POINTER = OPENMPT_ERROR_BASE + 103
OPENMPT_ERROR_DOMAIN = OPENMPT_ERROR_BASE + 41
OPENMPT_ERROR_EXCEPTION = OPENMPT_ERROR_BASE + 11
OPENMPT_ERROR_FUNC_RESULT_LOG = 1 << 0
OPENMPT_ERROR_FUNC_RESULT_STORE = 1 << 1
OPENMPT_ERROR_FUNC_RESULT_DEFAULT = (
    OPENMPT_ERROR_FUNC_RESULT_LOG | OPENMPT_ERROR_FUNC_RESULT_STORE
)
OPENMPT_ERROR_FUNC_RESULT_NONE = 0
OPENMPT_ERROR_GENERAL = OPENMPT_ERROR_BASE + 101
OPENMPT_ERROR_INVALID_ARGUMENT = OPENMPT_ERROR_BASE + 44
OPENMPT_ERROR_INVALID_MODULE_POINTER = OPENMPT_ERROR_BASE + 102
OPENMPT_ERROR_LENGTH = OPENMPT_ERROR_BASE + 42
OPENMPT_ERROR_LOGIC = OPENMPT_ERROR_BASE + 40
OPENMPT_ERROR_OK = 0
OPENMPT_ERROR_OUT_OF_MEMORY = OPENMPT_ERROR_BASE + 21
OPENMPT_ERROR_OUT_OF_RANGE = OPENMPT_ERROR_BASE + 43
OPENMPT_ERROR_OVERFLOW = OPENMPT_ERROR_BASE + 32
OPENMPT_ERROR_RANGE = OPENMPT_ERROR_BASE + 31
OPENMPT_ERROR_RUNTIME = OPENMPT_ERROR_BASE + 30
OPENMPT_ERROR_UNDERFLOW = OPENMPT_ERROR_BASE + 33
OPENMPT_ERROR_UNKNOWN = OPENMPT_ERROR_BASE + 1
OPENMPT_PROBE_FILE_HEADER_FLAGS_CONTAINERS = 2
OPENMPT_PROBE_FILE_HEADER_FLAGS_MODULES = 1
OPENMPT_PROBE_FILE_HEADER_FLAGS_DEFAULT = (
    OPENMPT_PROBE_FILE_HEADER_FLAGS_MODULES | OPENMPT_PROBE_FILE_HEADER_FLAGS_CONTAINERS
)
OPENMPT_PROBE_FILE_HEADER_FLAGS_NONE = 0
OPENMPT_PROBE_FILE_HEADER_RESULT_ERROR = -255
OPENMPT_PROBE_FILE_HEADER_RESULT_FAILURE = 0
OPENMPT_PROBE_FILE_HEADER_RESULT_SUCCESS = 1
OPENMPT_PROBE_FILE_HEADER_RESULT_WANTMOREDATA = -1
OPENMPT_STREAM_SEEK_CUR = 1
OPENMPT_STREAM_SEEK_END = 2
OPENMPT_STREAM_SEEK_SET = 0
LIBOPENMPT_DEPRECATED_STRING = lambda string: string
OPENMPT_STRING_BUILD = LIBOPENMPT_DEPRECATED_STRING("build")
OPENMPT_STRING_CONTACT = LIBOPENMPT_DEPRECATED_STRING("contact")
OPENMPT_STRING_CORE_VERSION = LIBOPENMPT_DEPRECATED_STRING("core_version")
OPENMPT_STRING_CREDITS = LIBOPENMPT_DEPRECATED_STRING("credits")
OPENMPT_STRING_LIBRARY_FEATURES = LIBOPENMPT_DEPRECATED_STRING("library_features")
OPENMPT_STRING_LIBRARY_VERSION = LIBOPENMPT_DEPRECATED_STRING("library_version")
OPENMPT_STRING_LICENSE = LIBOPENMPT_DEPRECATED_STRING("license")


openmpt_error_func = ctypes.CFUNCTYPE(c_int, c_int, c_void_p)

openmpt_log_func = ctypes.CFUNCTYPE(None, c_char_p, c_void_p)

openmpt_stream_read_func = ctypes.CFUNCTYPE(c_size_t, c_void_p, c_void_p, c_size_t)

openmpt_stream_seek_func = ctypes.CFUNCTYPE(c_int, c_void_p, c_int64, c_int)

openmpt_stream_tell_func = ctypes.CFUNCTYPE(c_int64, c_void_p)

openmpt_module = c_void_p

openmpt_module_initial_ctl = c_void_p

openmpt_stream_buffer = c_void_p

openmpt_stream_callbacks = c_void_p


openmpt_could_open_probability = LIBOPENMPT.openmpt_could_open_probability
openmpt_could_open_probability.argtypes = [
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_double,  # effort
    c_void_p,  # logfunc
    c_void_p,  # user
]
openmpt_could_open_probability.restype = c_double

openmpt_could_open_probability2 = LIBOPENMPT.openmpt_could_open_probability2
openmpt_could_open_probability2.argtypes = [
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_double,  # effort
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
]
openmpt_could_open_probability2.restype = c_double

openmpt_could_open_propability = LIBOPENMPT.openmpt_could_open_propability
openmpt_could_open_propability.argtypes = [
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_double,  # effort
    c_void_p,  # logfunc
    c_void_p,  # user
]
openmpt_could_open_propability.restype = c_double

openmpt_error_func_default = LIBOPENMPT.openmpt_error_func_default
openmpt_error_func_default.argtypes = [
    c_int,  # error
    c_void_p,  # user
]
openmpt_error_func_default.restype = c_int

openmpt_error_func_errno = LIBOPENMPT.openmpt_error_func_errno
openmpt_error_func_errno.argtypes = [
    c_int,  # error
    c_void_p,  # user
]
openmpt_error_func_errno.restype = c_int

openmpt_error_func_errno_userdata = LIBOPENMPT.openmpt_error_func_errno_userdata
openmpt_error_func_errno_userdata.argtypes = [
    POINTER(c_int),  # error
]
openmpt_error_func_errno_userdata.restype = c_void_p

openmpt_error_func_ignore = LIBOPENMPT.openmpt_error_func_ignore
openmpt_error_func_ignore.argtypes = [
    c_int,  # error
    c_void_p,  # user
]
openmpt_error_func_ignore.restype = c_int

openmpt_error_func_log = LIBOPENMPT.openmpt_error_func_log
openmpt_error_func_log.argtypes = [
    c_int,  # error
    c_void_p,  # user
]
openmpt_error_func_log.restype = c_int

openmpt_error_func_store = LIBOPENMPT.openmpt_error_func_store
openmpt_error_func_store.argtypes = [
    c_int,  # error
    c_void_p,  # user
]
openmpt_error_func_store.restype = c_int

openmpt_error_is_transient = LIBOPENMPT.openmpt_error_is_transient
openmpt_error_is_transient.argtypes = [
    c_int,  # error
]
openmpt_error_is_transient.restype = c_int

openmpt_error_string = LIBOPENMPT.openmpt_error_string
openmpt_error_string.argtypes = [
    c_int,  # error
]
openmpt_error_string.restype = c_char_p

openmpt_free_string = LIBOPENMPT.openmpt_free_string
openmpt_free_string.argtypes = [
    c_char_p,  # str
]
openmpt_free_string.restype = None

openmpt_get_core_version = LIBOPENMPT.openmpt_get_core_version
openmpt_get_core_version.restype = c_uint32

openmpt_get_library_version = LIBOPENMPT.openmpt_get_library_version
openmpt_get_library_version.restype = c_uint32

openmpt_get_string = LIBOPENMPT.openmpt_get_string
openmpt_get_string.argtypes = [
    c_char_p,  # key
]
openmpt_get_string.restype = c_char_p

openmpt_get_supported_extensions = LIBOPENMPT.openmpt_get_supported_extensions
openmpt_get_supported_extensions.restype = c_char_p

openmpt_is_extension_supported = LIBOPENMPT.openmpt_is_extension_supported
openmpt_is_extension_supported.argtypes = [
    c_char_p,  # extension
]
openmpt_is_extension_supported.restype = c_int

openmpt_log_func_default = LIBOPENMPT.openmpt_log_func_default
openmpt_log_func_default.argtypes = [
    c_char_p,  # message
    c_void_p,  # user
]
openmpt_log_func_default.restype = None

openmpt_log_func_silent = LIBOPENMPT.openmpt_log_func_silent
openmpt_log_func_silent.argtypes = [
    c_char_p,  # message
    c_void_p,  # user
]
openmpt_log_func_silent.restype = None

openmpt_module_create = LIBOPENMPT.openmpt_module_create
openmpt_module_create.argtypes = [
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_void_p,  # logfunc
    c_void_p,  # loguser
    POINTER(c_void_p),  # ctls
]
openmpt_module_create.restype = POINTER(openmpt_module)

openmpt_module_create2 = LIBOPENMPT.openmpt_module_create2
openmpt_module_create2.argtypes = [
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
    POINTER(c_void_p),  # ctls
]
openmpt_module_create2.restype = POINTER(openmpt_module)

openmpt_module_create_from_memory = LIBOPENMPT.openmpt_module_create_from_memory
openmpt_module_create_from_memory.argtypes = [
    c_void_p,  # filedata
    c_size_t,  # filesize
    c_void_p,  # logfunc
    c_void_p,  # loguser
    POINTER(c_void_p),  # ctls
]
openmpt_module_create_from_memory.restype = POINTER(openmpt_module)

openmpt_module_create_from_memory2 = LIBOPENMPT.openmpt_module_create_from_memory2
openmpt_module_create_from_memory2.argtypes = [
    c_void_p,  # filedata
    c_size_t,  # filesize
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
    c_void_p,  # ctls
]
openmpt_module_create_from_memory2.restype = POINTER(openmpt_module)

openmpt_module_ctl_get = LIBOPENMPT.openmpt_module_ctl_get
openmpt_module_ctl_get.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
]
openmpt_module_ctl_get.restype = c_char_p

openmpt_module_ctl_get_boolean = LIBOPENMPT.openmpt_module_ctl_get_boolean
openmpt_module_ctl_get_boolean.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
]
openmpt_module_ctl_get_boolean.restype = c_int

openmpt_module_ctl_get_floatingpoint = LIBOPENMPT.openmpt_module_ctl_get_floatingpoint
openmpt_module_ctl_get_floatingpoint.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
]
openmpt_module_ctl_get_floatingpoint.restype = c_double

openmpt_module_ctl_get_integer = LIBOPENMPT.openmpt_module_ctl_get_integer
openmpt_module_ctl_get_integer.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
]
openmpt_module_ctl_get_integer.restype = c_int64

openmpt_module_ctl_get_text = LIBOPENMPT.openmpt_module_ctl_get_text
openmpt_module_ctl_get_text.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
]
openmpt_module_ctl_get_text.restype = c_char_p

openmpt_module_ctl_set = LIBOPENMPT.openmpt_module_ctl_set
openmpt_module_ctl_set.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
    c_char_p,  # value
]
openmpt_module_ctl_set.restype = c_int

openmpt_module_ctl_set_boolean = LIBOPENMPT.openmpt_module_ctl_set_boolean
openmpt_module_ctl_set_boolean.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
    c_int,  # value
]
openmpt_module_ctl_set_boolean.restype = c_int

openmpt_module_ctl_set_floatingpoint = LIBOPENMPT.openmpt_module_ctl_set_floatingpoint
openmpt_module_ctl_set_floatingpoint.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
    c_double,  # value
]
openmpt_module_ctl_set_floatingpoint.restype = c_int

openmpt_module_ctl_set_integer = LIBOPENMPT.openmpt_module_ctl_set_integer
openmpt_module_ctl_set_integer.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
    c_int64,  # value
]
openmpt_module_ctl_set_integer.restype = c_int

openmpt_module_ctl_set_text = LIBOPENMPT.openmpt_module_ctl_set_text
openmpt_module_ctl_set_text.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # ctl
    c_char_p,  # value
]
openmpt_module_ctl_set_text.restype = c_int

openmpt_module_destroy = LIBOPENMPT.openmpt_module_destroy
openmpt_module_destroy.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_destroy.restype = None

openmpt_module_error_clear = LIBOPENMPT.openmpt_module_error_clear
openmpt_module_error_clear.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_error_clear.restype = None

openmpt_module_error_get_last = LIBOPENMPT.openmpt_module_error_get_last
openmpt_module_error_get_last.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_error_get_last.restype = c_int

openmpt_module_error_get_last_message = (
    LIBOPENMPT.openmpt_module_error_get_last_message
)
openmpt_module_error_get_last_message.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_error_get_last_message.restype = c_char_p

openmpt_module_error_set_last = LIBOPENMPT.openmpt_module_error_set_last
openmpt_module_error_set_last.argtypes = [
    POINTER(c_void_p),  # mod
    c_int,  # error
]
openmpt_module_error_set_last.restype = None

openmpt_module_format_pattern_row_channel = (
    LIBOPENMPT.openmpt_module_format_pattern_row_channel
)
openmpt_module_format_pattern_row_channel.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
    c_int32,  # row
    c_int32,  # channel
    c_size_t,  # width
    c_int,  # pad
]
openmpt_module_format_pattern_row_channel.restype = c_char_p

openmpt_module_format_pattern_row_channel_command = (
    LIBOPENMPT.openmpt_module_format_pattern_row_channel_command
)
openmpt_module_format_pattern_row_channel_command.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
    c_int32,  # row
    c_int32,  # channel
    c_int,  # command
]
openmpt_module_format_pattern_row_channel_command.restype = c_char_p

openmpt_module_get_channel_name = LIBOPENMPT.openmpt_module_get_channel_name
openmpt_module_get_channel_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_channel_name.restype = c_char_p

openmpt_module_get_ctls = LIBOPENMPT.openmpt_module_get_ctls
openmpt_module_get_ctls.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_ctls.restype = c_char_p

openmpt_module_get_current_channel_vu_left = (
    LIBOPENMPT.openmpt_module_get_current_channel_vu_left
)
openmpt_module_get_current_channel_vu_left.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # channel
]
openmpt_module_get_current_channel_vu_left.restype = c_float

openmpt_module_get_current_channel_vu_mono = (
    LIBOPENMPT.openmpt_module_get_current_channel_vu_mono
)
openmpt_module_get_current_channel_vu_mono.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # channel
]
openmpt_module_get_current_channel_vu_mono.restype = c_float

openmpt_module_get_current_channel_vu_rear_left = (
    LIBOPENMPT.openmpt_module_get_current_channel_vu_rear_left
)
openmpt_module_get_current_channel_vu_rear_left.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # channel
]
openmpt_module_get_current_channel_vu_rear_left.restype = c_float

openmpt_module_get_current_channel_vu_rear_right = (
    LIBOPENMPT.openmpt_module_get_current_channel_vu_rear_right
)
openmpt_module_get_current_channel_vu_rear_right.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # channel
]
openmpt_module_get_current_channel_vu_rear_right.restype = c_float

openmpt_module_get_current_channel_vu_right = (
    LIBOPENMPT.openmpt_module_get_current_channel_vu_right
)
openmpt_module_get_current_channel_vu_right.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # channel
]
openmpt_module_get_current_channel_vu_right.restype = c_float

openmpt_module_get_current_estimated_bpm = (
    LIBOPENMPT.openmpt_module_get_current_estimated_bpm
)
openmpt_module_get_current_estimated_bpm.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_estimated_bpm.restype = c_double

openmpt_module_get_current_order = LIBOPENMPT.openmpt_module_get_current_order
openmpt_module_get_current_order.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_order.restype = c_int32

openmpt_module_get_current_pattern = LIBOPENMPT.openmpt_module_get_current_pattern
openmpt_module_get_current_pattern.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_pattern.restype = c_int32

openmpt_module_get_current_playing_channels = (
    LIBOPENMPT.openmpt_module_get_current_playing_channels
)
openmpt_module_get_current_playing_channels.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_playing_channels.restype = c_int32

openmpt_module_get_current_row = LIBOPENMPT.openmpt_module_get_current_row
openmpt_module_get_current_row.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_row.restype = c_int32

openmpt_module_get_current_speed = LIBOPENMPT.openmpt_module_get_current_speed
openmpt_module_get_current_speed.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_speed.restype = c_int32

openmpt_module_get_current_tempo = LIBOPENMPT.openmpt_module_get_current_tempo
openmpt_module_get_current_tempo.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_current_tempo.restype = c_int32

openmpt_module_get_duration_seconds = LIBOPENMPT.openmpt_module_get_duration_seconds
openmpt_module_get_duration_seconds.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_duration_seconds.restype = c_double

openmpt_module_get_instrument_name = (
    LIBOPENMPT.openmpt_module_get_instrument_name
)
openmpt_module_get_instrument_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_instrument_name.restype = c_char_p

openmpt_module_get_metadata = LIBOPENMPT.openmpt_module_get_metadata
openmpt_module_get_metadata.argtypes = [
    POINTER(c_void_p),  # mod
    c_char_p,  # key
]
openmpt_module_get_metadata.restype = c_char_p

openmpt_module_get_metadata_keys = LIBOPENMPT.openmpt_module_get_metadata_keys
openmpt_module_get_metadata_keys.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_metadata_keys.restype = c_char_p

openmpt_module_get_num_channels = LIBOPENMPT.openmpt_module_get_num_channels
openmpt_module_get_num_channels.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_channels.restype = c_int32

openmpt_module_get_num_instruments = LIBOPENMPT.openmpt_module_get_num_instruments
openmpt_module_get_num_instruments.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_instruments.restype = c_int32

openmpt_module_get_num_orders = LIBOPENMPT.openmpt_module_get_num_orders
openmpt_module_get_num_orders.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_orders.restype = c_int32

openmpt_module_get_num_patterns = LIBOPENMPT.openmpt_module_get_num_patterns
openmpt_module_get_num_patterns.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_patterns.restype = c_int32

openmpt_module_get_num_samples = LIBOPENMPT.openmpt_module_get_num_samples
openmpt_module_get_num_samples.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_samples.restype = c_int32

openmpt_module_get_num_subsongs = LIBOPENMPT.openmpt_module_get_num_subsongs
openmpt_module_get_num_subsongs.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_num_subsongs.restype = c_int32

openmpt_module_get_order_name = LIBOPENMPT.openmpt_module_get_order_name
openmpt_module_get_order_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_order_name.restype = c_char_p

openmpt_module_get_order_pattern = LIBOPENMPT.openmpt_module_get_order_pattern
openmpt_module_get_order_pattern.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # order
]
openmpt_module_get_order_pattern.restype = c_int32

openmpt_module_get_pattern_name = LIBOPENMPT.openmpt_module_get_pattern_name
openmpt_module_get_pattern_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_pattern_name.restype = c_char_p

openmpt_module_get_pattern_num_rows = LIBOPENMPT.openmpt_module_get_pattern_num_rows
openmpt_module_get_pattern_num_rows.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
]
openmpt_module_get_pattern_num_rows.restype = c_int32

openmpt_module_get_pattern_row_channel_command = (
    LIBOPENMPT.openmpt_module_get_pattern_row_channel_command
)
openmpt_module_get_pattern_row_channel_command.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
    c_int32,  # row
    c_int32,  # channel
    c_int,  # command
]
openmpt_module_get_pattern_row_channel_command.restype = c_uint8

openmpt_module_get_position_seconds = LIBOPENMPT.openmpt_module_get_position_seconds
openmpt_module_get_position_seconds.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_position_seconds.restype = c_double

openmpt_module_get_render_param = LIBOPENMPT.openmpt_module_get_render_param
openmpt_module_get_render_param.argtypes = [
    POINTER(c_void_p),  # mod
    c_int,  # param
    POINTER(c_int32),  # value
]
openmpt_module_get_render_param.restype = c_int

openmpt_module_get_repeat_count = LIBOPENMPT.openmpt_module_get_repeat_count
openmpt_module_get_repeat_count.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_repeat_count.restype = c_int32

openmpt_module_get_sample_name = LIBOPENMPT.openmpt_module_get_sample_name
openmpt_module_get_sample_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_sample_name.restype = c_char_p

openmpt_module_get_selected_subsong = LIBOPENMPT.openmpt_module_get_selected_subsong
openmpt_module_get_selected_subsong.argtypes = [
    POINTER(c_void_p),  # mod
]
openmpt_module_get_selected_subsong.restype = c_int32

openmpt_module_get_subsong_name = LIBOPENMPT.openmpt_module_get_subsong_name
openmpt_module_get_subsong_name.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # index
]
openmpt_module_get_subsong_name.restype = c_char_p

openmpt_module_highlight_pattern_row_channel = (
    LIBOPENMPT.openmpt_module_highlight_pattern_row_channel
)
openmpt_module_highlight_pattern_row_channel.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
    c_int32,  # row
    c_int32,  # channel
    c_size_t,  # width
    c_int,  # pad
]
openmpt_module_highlight_pattern_row_channel.restype = c_char_p

openmpt_module_highlight_pattern_row_channel_command = (
    LIBOPENMPT.openmpt_module_highlight_pattern_row_channel_command
)
openmpt_module_highlight_pattern_row_channel_command.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # pattern
    c_int32,  # row
    c_int32,  # channel
    c_int,  # command
]
openmpt_module_highlight_pattern_row_channel_command.restype = c_char_p

openmpt_module_read_float_mono = LIBOPENMPT.openmpt_module_read_float_mono
openmpt_module_read_float_mono.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_float),  # mono
]
openmpt_module_read_float_mono.restype = c_size_t

openmpt_module_read_float_quad = LIBOPENMPT.openmpt_module_read_float_quad
openmpt_module_read_float_quad.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_float),  # left
    POINTER(c_float),  # right
    POINTER(c_float),  # rear_left
    POINTER(c_float),  # rear_right
]
openmpt_module_read_float_quad.restype = c_size_t

openmpt_module_read_float_stereo = LIBOPENMPT.openmpt_module_read_float_stereo
openmpt_module_read_float_stereo.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_float),  # left
    POINTER(c_float),  # right
]
openmpt_module_read_float_stereo.restype = c_size_t

openmpt_module_read_interleaved_float_quad = (
    LIBOPENMPT.openmpt_module_read_interleaved_float_quad
)
openmpt_module_read_interleaved_float_quad.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_float),  # interleaved_quad
]
openmpt_module_read_interleaved_float_quad.restype = c_size_t

openmpt_module_read_interleaved_float_stereo = (
    LIBOPENMPT.openmpt_module_read_interleaved_float_stereo
)
openmpt_module_read_interleaved_float_stereo.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_float),  # interleaved_stereo
]
openmpt_module_read_interleaved_float_stereo.restype = c_size_t

openmpt_module_read_interleaved_quad = LIBOPENMPT.openmpt_module_read_interleaved_quad
openmpt_module_read_interleaved_quad.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_int16),  # interleaved_quad
]
openmpt_module_read_interleaved_quad.restype = c_size_t

openmpt_module_read_interleaved_stereo = (
    LIBOPENMPT.openmpt_module_read_interleaved_stereo
)
openmpt_module_read_interleaved_stereo.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_int16),  # interleaved_stereo
]
openmpt_module_read_interleaved_stereo.restype = c_size_t

openmpt_module_read_mono = LIBOPENMPT.openmpt_module_read_mono
openmpt_module_read_mono.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_int16),  # mono
]
openmpt_module_read_mono.restype = c_size_t

openmpt_module_read_quad = LIBOPENMPT.openmpt_module_read_quad
openmpt_module_read_quad.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_int16),  # left
    POINTER(c_int16),  # right
    POINTER(c_int16),  # rear_left
    POINTER(c_int16),  # rear_right
]
openmpt_module_read_quad.restype = c_size_t

openmpt_module_read_stereo = LIBOPENMPT.openmpt_module_read_stereo
openmpt_module_read_stereo.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # samplerate
    c_size_t,  # count
    POINTER(c_int16),  # left
    POINTER(c_int16),  # right
]
openmpt_module_read_stereo.restype = c_size_t

openmpt_module_select_subsong = LIBOPENMPT.openmpt_module_select_subsong
openmpt_module_select_subsong.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # subsong
]
openmpt_module_select_subsong.restype = c_int

openmpt_module_set_error_func = LIBOPENMPT.openmpt_module_set_error_func
openmpt_module_set_error_func.argtypes = [
    POINTER(c_void_p),  # mod
    c_void_p,  # errfunc
    c_void_p,  # erruser
]
openmpt_module_set_error_func.restype = None

openmpt_module_set_log_func = LIBOPENMPT.openmpt_module_set_log_func
openmpt_module_set_log_func.argtypes = [
    POINTER(c_void_p),  # mod
    c_void_p,  # logfunc
    c_void_p,  # loguser
]
openmpt_module_set_log_func.restype = None

openmpt_module_set_position_order_row = LIBOPENMPT.openmpt_module_set_position_order_row
openmpt_module_set_position_order_row.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # order
    c_int32,  # row
]
openmpt_module_set_position_order_row.restype = c_double

openmpt_module_set_position_seconds = LIBOPENMPT.openmpt_module_set_position_seconds
openmpt_module_set_position_seconds.argtypes = [
    POINTER(c_void_p),  # mod
    c_double,  # seconds
]
openmpt_module_set_position_seconds.restype = c_double

openmpt_module_set_render_param = LIBOPENMPT.openmpt_module_set_render_param
openmpt_module_set_render_param.argtypes = [
    POINTER(c_void_p),  # mod
    c_int,  # param
    c_int32,  # value
]
openmpt_module_set_render_param.restype = c_int

openmpt_module_set_repeat_count = LIBOPENMPT.openmpt_module_set_repeat_count
openmpt_module_set_repeat_count.argtypes = [
    POINTER(c_void_p),  # mod
    c_int32,  # repeat_count
]
openmpt_module_set_repeat_count.restype = c_int

openmpt_probe_file_header = LIBOPENMPT.openmpt_probe_file_header
openmpt_probe_file_header.argtypes = [
    c_uint64,  # flags
    c_void_p,  # data
    c_size_t,  # size
    c_uint64,  # filesize
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
]
openmpt_probe_file_header.restype = c_int

openmpt_probe_file_header_from_stream = LIBOPENMPT.openmpt_probe_file_header_from_stream
openmpt_probe_file_header_from_stream.argtypes = [
    c_uint64,  # flags
    c_void_p,  # stream_callbacks
    c_void_p,  # stream
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
]
openmpt_probe_file_header_from_stream.restype = c_int

openmpt_probe_file_header_get_recommended_size = (
    LIBOPENMPT.openmpt_probe_file_header_get_recommended_size
)
openmpt_probe_file_header_get_recommended_size.restype = c_size_t

openmpt_probe_file_header_without_filesize = (
    LIBOPENMPT.openmpt_probe_file_header_without_filesize
)
openmpt_probe_file_header_without_filesize.argtypes = [
    c_uint64,  # flags
    c_void_p,  # data
    c_size_t,  # size
    c_void_p,  # logfunc
    c_void_p,  # loguser
    c_void_p,  # errfunc
    c_void_p,  # erruser
    POINTER(c_int),  # error
    POINTER(c_char_p),  # error_message
]
openmpt_probe_file_header_without_filesize.restype = c_int

# static stuff below here, needs fixing

# openmpt_stream_buffer_init = LIBOPENMPT.openmpt_stream_buffer_init
# openmpt_stream_buffer_init.argtypes = [
#     c_void_p,  # buffer
#     c_void_p,  # file_data
#     c_int64,  # file_size
# ]
# openmpt_stream_buffer_init.restype = None
# openmpt_stream_buffer_init_address = getattr(LIBOPENMPT, "openmpt_stream_buffer_init")
# openmpt_stream_buffer_init_func = ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_int64)
# openmpt_stream_buffer_init_cast = openmpt_stream_buffer_init_func(
#     openmpt_stream_buffer_init_address
# )
# openmpt_stream_buffer_init_cast.argtypes = [c_void_p, c_void_p, c_int64]


# def openmpt_stream_buffer_init_prefix_only(
#     buffer_, prefix_data_, prefix_size_, file_size_
# ):
#     openmpt_stream_buffer_init(buffer_, prefix_data_, file_size_)
#     buffer_.prefix_size = prefix_size_


# openmpt_stream_buffer_overflowed = lambda buffer_: buffer_.overflow

# openmpt_stream_buffer_read_func = LIBOPENMPT.openmpt_stream_buffer_read_func
# openmpt_stream_buffer_read_func.argtypes = [
#     c_void_p,  # stream
#     c_void_p,  # dst
#     c_size_t,  # bytes
# ]
# openmpt_stream_buffer_read_func.restype = c_size_t
# openmpt_stream_buffer_read_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_buffer_read_func"
# )
# openmpt_stream_buffer_read_func_func = ctypes.CFUNCTYPE(
#     c_size_t, c_void_p, c_void_p, c_size_t
# )
# openmpt_stream_buffer_read_func_cast = openmpt_stream_buffer_read_func_func(
#     openmpt_stream_buffer_read_func_address
# )
# openmpt_stream_buffer_read_func_cast.argtypes = [c_void_p, c_void_p, c_size_t]

# openmpt_stream_buffer_seek_func = LIBOPENMPT.openmpt_stream_buffer_seek_func
# openmpt_stream_buffer_seek_func.argtypes = [
#     c_void_p,  # stream
#     c_int64,  # offset
#     c_int,  # whence
# ]
# openmpt_stream_buffer_seek_func.restype = c_int
# openmpt_stream_buffer_seek_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_buffer_seek_func"
# )
# openmpt_stream_buffer_seek_func_func = ctypes.CFUNCTYPE(c_int, c_void_p, c_int64, c_int)
# openmpt_stream_buffer_seek_func_cast = openmpt_stream_buffer_seek_func_func(
#     openmpt_stream_buffer_seek_func_address
# )
# openmpt_stream_buffer_seek_func_cast.argtypes = [c_void_p, c_int64, c_int]

# openmpt_stream_buffer_tell_func = LIBOPENMPT.openmpt_stream_buffer_tell_func
# openmpt_stream_buffer_tell_func.argtypes = [
#     c_void_p,  # stream
# ]
# openmpt_stream_buffer_tell_func.restype = c_int64
# openmpt_stream_buffer_tell_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_buffer_tell_func"
# )
# openmpt_stream_buffer_tell_func_func = ctypes.CFUNCTYPE(c_int64, c_void_p)
# openmpt_stream_buffer_tell_func_cast = openmpt_stream_buffer_tell_func_func(
#     openmpt_stream_buffer_tell_func_address
# )
# openmpt_stream_buffer_tell_func_cast.argtypes = [c_void_p]

# openmpt_stream_fd_read_func = LIBOPENMPT.openmpt_stream_fd_read_func
# openmpt_stream_fd_read_func.argtypes = [
#     c_void_p,  # stream
#     c_void_p,  # dst
#     c_size_t,  # bytes
# ]
# openmpt_stream_fd_read_func.restype = c_size_t
# openmpt_stream_fd_read_func_address = getattr(LIBOPENMPT, "openmpt_stream_fd_read_func")
# openmpt_stream_fd_read_func_func = ctypes.CFUNCTYPE(
#     c_size_t, c_void_p, c_void_p, c_size_t
# )
# openmpt_stream_fd_read_func_cast = openmpt_stream_fd_read_func_func(
#     openmpt_stream_fd_read_func_address
# )
# openmpt_stream_fd_read_func_cast.argtypes = [c_void_p, c_void_p, c_size_t]

# openmpt_stream_file_read_func = LIBOPENMPT.openmpt_stream_file_read_func
# openmpt_stream_file_read_func.argtypes = [
#     c_void_p,  # stream
#     c_void_p,  # dst
#     c_size_t,  # bytes
# ]
# openmpt_stream_file_read_func.restype = c_size_t
# openmpt_stream_file_read_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_file_read_func"
# )
# openmpt_stream_file_read_func_func = ctypes.CFUNCTYPE(
#     c_size_t, c_void_p, c_void_p, c_size_t
# )
# openmpt_stream_file_read_func_cast = openmpt_stream_file_read_func_func(
#     openmpt_stream_file_read_func_address
# )
# openmpt_stream_file_read_func_cast.argtypes = [c_void_p, c_void_p, c_size_t]

# openmpt_stream_file_seek_func = LIBOPENMPT.openmpt_stream_file_seek_func
# openmpt_stream_file_seek_func.argtypes = [
#     c_void_p,  # stream
#     c_int64,  # offset
#     c_int,  # whence
# ]
# openmpt_stream_file_seek_func.restype = c_int
# openmpt_stream_file_seek_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_file_seek_func"
# )
# openmpt_stream_file_seek_func_func = ctypes.CFUNCTYPE(c_int, c_void_p, c_int64, c_int)
# openmpt_stream_file_seek_func_cast = openmpt_stream_file_seek_func_func(
#     openmpt_stream_file_seek_func_address
# )
# openmpt_stream_file_seek_func_cast.argtypes = [c_void_p, c_int64, c_int]

# openmpt_stream_file_tell_func = LIBOPENMPT.openmpt_stream_file_tell_func
# openmpt_stream_file_tell_func.argtypes = [
#     c_void_p,  # stream
# ]
# openmpt_stream_file_tell_func.restype = c_int64
# openmpt_stream_file_tell_func_address = getattr(
#     LIBOPENMPT, "openmpt_stream_file_tell_func"
# )
# openmpt_stream_file_tell_func_func = ctypes.CFUNCTYPE(c_int64, c_void_p)
# openmpt_stream_file_tell_func_cast = openmpt_stream_file_tell_func_func(
#     openmpt_stream_file_tell_func_address
# )
# openmpt_stream_file_tell_func_cast.argtypes = [c_void_p]

# openmpt_stream_get_buffer_callbacks = LIBOPENMPT.openmpt_stream_get_buffer_callbacks
# openmpt_stream_get_buffer_callbacks.restype = c_void_p
# openmpt_stream_get_buffer_callbacks_address = getattr(
#     LIBOPENMPT, "openmpt_stream_get_buffer_callbacks"
# )
# openmpt_stream_get_buffer_callbacks_func = ctypes.CFUNCTYPE(c_void_p, None)
# openmpt_stream_get_buffer_callbacks_cast = openmpt_stream_get_buffer_callbacks_func(
#     openmpt_stream_get_buffer_callbacks_address
# )
# openmpt_stream_get_buffer_callbacks_cast.argtypes = [None]

# openmpt_stream_get_fd_callbacks = LIBOPENMPT.openmpt_stream_get_fd_callbacks
# openmpt_stream_get_fd_callbacks.restype = c_void_p
# openmpt_stream_get_fd_callbacks_address = getattr(
#     LIBOPENMPT, "openmpt_stream_get_fd_callbacks"
# )
# openmpt_stream_get_fd_callbacks_func = ctypes.CFUNCTYPE(c_void_p, None)
# openmpt_stream_get_fd_callbacks_cast = openmpt_stream_get_fd_callbacks_func(
#     openmpt_stream_get_fd_callbacks_address
# )
# openmpt_stream_get_fd_callbacks_cast.argtypes = [None]

# openmpt_stream_get_file_callbacks = LIBOPENMPT.openmpt_stream_get_file_callbacks
# openmpt_stream_get_file_callbacks.restype = c_void_p
# openmpt_stream_get_file_callbacks_address = getattr(
#     LIBOPENMPT, "openmpt_stream_get_file_callbacks"
# )
# openmpt_stream_get_file_callbacks_func = ctypes.CFUNCTYPE(c_void_p, None)
# openmpt_stream_get_file_callbacks_cast = openmpt_stream_get_file_callbacks_func(
#     openmpt_stream_get_file_callbacks_address
# )
# openmpt_stream_get_file_callbacks_cast.argtypes = [None]
