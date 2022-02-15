from uaddef import *

libc = CDLL("/usr/lib/libc.so.6")

libc.free.argtypes = [c_void_p]

CDLL("/usr/lib/libbencodetools.so", mode=RTLD_GLOBAL)
libuade = CDLL("/usr/lib/libuade.so", mode=RTLD_GLOBAL)
libao = CDLL("/usr/lib/libao.so.4")

libuade.uade_new_state.argtypes = [c_void_p]
libuade.uade_new_state.restype = c_void_p

libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
libuade.uade_read_file.restype = c_void_p

libuade.uade_get_sampling_rate.argtypes = [c_void_p]
libuade.uade_get_sampling_rate.restype = c_int

libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]
libuade.uade_play.restype = c_int

libuade.uade_get_song_info.argtypes = [c_void_p]
libuade.uade_get_song_info.restype = POINTER(uade_song_info)

libuade.uade_read_notification.argtypes = [POINTER(uade_notification), c_void_p]

libuade.uade_cleanup_notification.argtypes = [POINTER(uade_notification)]

libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
libuade.uade_read.restype = c_ssize_t

libuade.uade_stop.argtypes = [c_void_p]

libuade.uade_cleanup_state.argtypes = [c_void_p]

libuade.uade_next_subsong.argtypes = [c_void_p]

libao.ao_open_live.argtypes = [c_int, c_void_p, c_void_p]
libao.ao_open_live.restype = c_void_p

libao.ao_close.argtypes = [c_void_p]
libao.ao_play.argtypes = [c_void_p, c_char_p, c_uint32]
