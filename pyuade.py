import sys
import time
from ctypes import *
import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QThread
import debugpy

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


class Uade(object):
    def __init__(self, *args):
        self.libc = CDLL("/usr/lib/libc.so.6")

        self.libc.free.argtypes = [c_void_p]

        CDLL("/usr/lib/libbencodetools.so", mode=RTLD_GLOBAL)
        self.libuade = CDLL("/usr/lib/libuade.so", mode=RTLD_GLOBAL)
        self.libao = CDLL("/usr/lib/libao.so.4")

        self.libuade.uade_new_state.argtypes = [c_void_p]
        self.libuade.uade_new_state.restype = c_void_p

        self.libuade.uade_read_file.argtypes = [POINTER(c_size_t), c_char_p]
        self.libuade.uade_read_file.restype = c_void_p

        self.libuade.uade_get_sampling_rate.argtypes = [c_void_p]
        self.libuade.uade_get_sampling_rate.restype = c_int

        self.libuade.uade_play.argtypes = [c_char_p, c_int, c_void_p]
        self.libuade.uade_play.restype = c_int

        self.libuade.uade_get_song_info.argtypes = [c_void_p]
        self.libuade.uade_get_song_info.restype = POINTER(uade_song_info)

        self.libuade.uade_read_notification.argtypes = [c_void_p, c_void_p]

        self.libuade.uade_read.argtypes = [c_void_p, c_size_t, c_void_p]
        self.libuade.uade_read.restype = c_ssize_t

        self.libuade.uade_stop.argtypes = [c_void_p]

        self.libuade.uade_cleanup_state.argtypes = [c_void_p]

        self.libao.ao_open_live.argtypes = [c_int, c_void_p, c_void_p]
        self.libao.ao_open_live.restype = c_void_p

        self.libao.ao_close.argtypes = [c_void_p]
        self.libao.ao_play.argtypes = [c_void_p, c_char_p, c_uint32]

        self.libao.ao_initialize()

    def load_song(self):
        size = c_size_t()
        buf = c_void_p()

        fname = "/home/andre/Musik/Retro/Games/the lost vikings 1.mod"

        buf = self.libuade.uade_read_file(
            byref(size), str.encode(fname))

        if not buf:
            print("Can not read file", fname)

        ret = self.libuade.uade_play(str.encode(fname), -1, self.state)

        if ret < 0:
            print("uade_play_from_buffer: error")
        elif ret == 0:
            print("Can not play", fname)

        self.libc.free(buf)

        info = self.libuade.uade_get_song_info(self.state).contents

        if info.formatname:
            print("Format name:", info.formatname.decode())
        if info.modulename:
            print("Module name:", info.modulename.decode())
        if info.playername:
            print("Player name:", info.playername.decode())

        print(
            f"subsongs: cur {info.subsongs.cur} min {info.subsongs.min} max {info.subsongs.max}")

    def init_play(self):
        print("Start playing")

        self.state = self.libuade.uade_new_state(None)

        if not self.state:
            print("uade_state is NULL")

        samplerate = self.libuade.uade_get_sampling_rate(self.state)

        self.load_song()

        format = ao_sample_format(
            2 * 8, self.libuade.uade_get_sampling_rate(self.state), 2, 4)

        driver = self.libao.ao_default_driver_id()

        self.libao_device = self.libao.ao_open_live(
            driver, byref(format), None)

        self.buf_len = 4096
        self.buf = (c_char * self.buf_len)()

        total = np.array([])
        # total = np.zeros(4096 * 1024, dtype=c_int16)

    def play(self):
        #running = True

        # while running:
        nbytes = self.libuade.uade_read(self.buf, self.buf_len, self.state)

        # pa = cast(buf, POINTER(c_char * buf_len))
        # a = np.frombuffer(pa.contents, dtype=np.int16)

        if nbytes < 0:
            print("Playback error.")
            return False
        elif nbytes == 0:
            print("Song end.")
            return False

        # total = np.append(total, a)

        if not self.libao.ao_play(self.libao_device, self.buf, nbytes):
            return False

        return True

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
    def stop(self):
        print("Stop playing")

        if self.libuade.uade_stop(self.state) != 0:
            print("uade_stop error")

        self.libuade.uade_cleanup_state(self.state)

        if self.libao.ao_close(self.libao_device) != 1:
            print("ao_close error")

        self.state = 0


class MyThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = True

    def run(self):
        debugpy.debug_this_thread()
        self.uade.init_play()

        while self.running:
            # sys.stdout.write('.')
            # sys.stdout.flush()
            # time.sleep(1)
            if not self.uade.play():
                self.running = False

        self.uade.stop()


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.play_btn = QtWidgets.QPushButton("Play")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.text)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.play_btn)
        h_layout.addWidget(self.stop_btn)

        layout.addLayout(h_layout)
        self.setLayout(layout)

        self.play_btn.clicked.connect(self.play)
        self.stop_btn.clicked.connect(self.stop)

        self.uade = Uade()

        self.thread = MyThread()

    @QtCore.Slot()
    def play(self):
        # self.uade.play()
        self.thread.uade = self.uade
        self.thread.start()
        self.thread.running = True

    @QtCore.Slot()
    def stop(self):
        self.thread.running = False
        self.thread.quit()
        # self.thread.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
