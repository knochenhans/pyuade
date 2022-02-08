from ctypes import *
import numpy as np
import sounddevice as sd
import soundfile as sf

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


def main():
    libc = CDLL("/usr/lib/libc.so.6")
    CDLL("/usr/lib/libbencodetools.so", mode=RTLD_GLOBAL)
    libuade = CDLL("/usr/lib/libuade.so", mode=RTLD_GLOBAL)
    libao = CDLL("/usr/lib/libao.so.4")

    libuade.uade_new_state.argtypes = [c_void_p]
    libuade.uade_new_state.restype = c_void_p

    state = libuade.uade_new_state(None)

    if not state:
        print("uade_state is NULL")

    # libuade.uade_set_debug.argtypes = [c_void_p]
    # libuade.uade_set_debug(state)

    libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
    libuade.uade_read_file.restype = c_void_p

    libuade.uade_get_sampling_rate.argtypes = [c_void_p]
    libuade.uade_get_sampling_rate.restype = c_int

    # libuade.audio_init.argtypes = [c_int]
    # libuade.audio_init.restype = c_int

    samplerate = libuade.uade_get_sampling_rate(state)

    size = c_size_t()
    buf = c_void_p()

    fname = "/home/andre/Musik/Retro/Games/the lost vikings 1.mod"

    buf = libuade.uade_read_file(
        byref(size), str.encode(fname))

    if not buf:
        print("Can not read file", fname)

    # libuade.uade_play_from_buffer.argtypes = [
    #     c_char_p, c_void_p, c_size_t, c_int, c_void_p]
    # libuade.uade_play_from_buffer.restype = c_int
    # ret = libuade.uade_play_from_buffer(None, buf, size, -1, state)

    libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]
    libuade.uade_play.restype = c_int
    ret = libuade.uade_play(str.encode(fname), -1, state)

    if ret < 0:
        print("uade_play_from_buffer: error")
    elif ret == 0:
        print("Can not play", fname)

    libc.free.argtypes = [c_void_p]
    libc.free(buf)

    libuade.uade_get_song_info.argtypes = [c_void_p]
    libuade.uade_get_song_info.restype = POINTER(uade_song_info)

    info = libuade.uade_get_song_info(state).contents

    if info.formatname:
        print("Format name:", info.formatname.decode())
    if info.modulename:
        print("Module name:", info.modulename.decode())
    if info.playername:
        print("Player name:", info.playername.decode())

    print(
        f"subsongs: cur {info.subsongs.cur} min {info.subsongs.min} max {info.subsongs.max}")

    libuade.uade_read_notification.argtypes = [c_void_p, c_void_p]

    libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
    libuade.uade_read.restype = c_ssize_t

    libao.ao_initialize()

    format = ao_sample_format(
        2 * 8, libuade.uade_get_sampling_rate(state), 2, 4)

    driver = libao.ao_default_driver_id()

    libao.ao_open_live.argtypes = [c_int, c_void_p, c_void_p]
    libao.ao_open_live.restype = c_void_p

    libao_device = libao.ao_open_live(driver, byref(format), None)

    buf_len = 4096
    buf = (c_char * buf_len)()

    total = np.array([])
    #total = np.zeros(4096 * 1024, dtype=c_int16)

    running = True

    while running:
        nbytes = libuade.uade_read(buf, buf_len, state)

        # pa = cast(buf, POINTER(c_char * buf_len))
        # a = np.frombuffer(pa.contents, dtype=np.int16)

        if nbytes < 0:
            print("Playback error.")
            running = False
        elif nbytes == 0:
            print("Song end.")
            running = False

        libao.ao_play.argtypes = [c_void_p, c_char_p, c_uint32]

        # total = np.append(total, a)

        play = libao.ao_play(libao_device, buf, nbytes)

    # cast(buf2, POINTER(c_char))

    # sd.play(total, 44100)
    # sd.wait()

    # for x in range(100):

    #     pa = cast(buf2, POINTER(c_char * 4096))
    #     a = np.frombuffer(pa.contents, dtype=np.int16)

        # if x >= 6:
        #     for i in range(16):
        #         print(a[i], " - ", format(a[i], '#016b'))
        # total = np.append(total, a)
        
    # def callback(outdata, frames, time, status):
    #     data = wf.buffer_read(frames, dtype='float32')
    #     if len(data) <= 0:
    #         raise sd.CallbackAbort
    #     if len(outdata) > len(data):
    #         raise sd.CallbackAbort  # wrong obviously
    #     outdata[:] = data

    # with sd.RawOutputStream(channels=wf.channels,
    #                         callback=callback) as stream:
    #     while stream.active:
    #         continue


if __name__ == "__main__":
    main()
