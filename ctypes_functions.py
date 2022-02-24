from ctypes import *
from ctypes import util
from ctypes_classes import *
import platform

if platform.system() == "Linux":
    # libc = CDLL(None)
    # libc = CDLL("/usr/lib/libc.so.6")

    # Load libbencodetools as requirement for libuade
    CDLL("libbencodetools.so", mode=RTLD_GLOBAL)

    libuade = CDLL("libuade.so", mode=RTLD_GLOBAL)
    libao = CDLL("libao.so")
elif platform.system() == "Windows":
    # TODO
    # libc = CDLL(None)

    # class FILE(Structure):
    #     _fields_ = [
    #         ("_ptr", c_char_p),
    #         ("_cnt", c_int),
    #         ("_base", c_char_p),
    #         ("_flag", c_int),
    #         ("_file", c_int),
    #         ("_charbuf", c_int),
    #         ("_bufsize", c_int),
    #         ("_tmpfname", c_char_p),
    #     ]

    # # Gives you the name of the library that you should really use (and then load through ctypes.CDLL
    # msvcrt = CDLL(util.find_msvcrt())
    # libc = msvcrt # libc was used in the original example in _redirect_stdout()
    # iob_func = msvcrt.__iob_func
    # iob_func.restype = POINTER(FILE)
    # iob_func.argtypes = []

    pass

# libc.free.argtypes = [c_void_p]

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
libuade.uade_seek_samples.argtypes = [c_int, c_int, c_int, c_void_p]

libuade.uade_is_seeking.argtypes = [c_void_p]

libuade.uade_get_event.argtypes = [c_void_p, c_void_p]

libuade.uade_get_fd.argtypes = [c_void_p]

libuade.uade_event_name.argtypes = [c_void_p]
libuade.uade_event_name.restype = c_char_p

libuade.uade_song_info.argtypes = [c_char_p, c_uint, c_char_p, c_int]

# libao

libao.ao_open_live.argtypes = [c_int, c_void_p, c_void_p]
libao.ao_open_live.restype = c_void_p

libao.ao_close.argtypes = [c_void_p]
libao.ao_play.argtypes = [c_void_p, c_char_p, c_uint32]
