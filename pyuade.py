import sys
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QFileDialog, QListWidgetItem
import debugpy
from uaddef import *
from externallibs import *

class Pyuade(object):
    def __init__(self, *args):
        libao.ao_initialize()

    def load_song(self, fname):
        size = c_size_t()
        buf = c_void_p()

        buf = libuade.uade_read_file(
            byref(size), str.encode(fname))

        if not buf:
            print("Can not read file", fname)

        ret = libuade.uade_play(str.encode(fname), -1, self.state)

        if ret < 0:
            print("uade_play_from_buffer: error")
        elif ret == 0:
            print("Can not play", fname)

        libc.free(buf)

        info = libuade.uade_get_song_info(self.state).contents

        if info.formatname:
            print("Format name:", info.formatname.decode())
        if info.modulename:
            print("Module name:", info.modulename.decode())
        if info.playername:
            print("Player name:", info.playername.decode())

        print(
            f"subsongs: cur {info.subsongs.cur} min {info.subsongs.min} max {info.subsongs.max}")

    def init_play(self, fname):
        print("Start playing")

        self.state = libuade.uade_new_state(None)

        if not self.state:
            print("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        self.load_song(fname)

        format = ao_sample_format(
            2 * 8, libuade.uade_get_sampling_rate(self.state), 2, 4)

        driver = libao.ao_default_driver_id()

        self.libao_device = libao.ao_open_live(
            driver, byref(format), None)

        self.buf_len = 4096
        self.buf = (c_char * self.buf_len)()

        # total = np.array([])
        # total = np.zeros(4096 * 1024, dtype=c_int16)

    def play(self):
        nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

        # pa = cast(buf, POINTER(c_char * buf_len))
        # a = np.frombuffer(pa.contents, dtype=np.int16)

        if nbytes < 0:
            print("Playback error.")
            return False
        elif nbytes == 0:
            print("Song end.")
            return False

        # total = np.append(total, a)

        if not libao.ao_play(self.libao_device, self.buf, nbytes):
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

        if libuade.uade_stop(self.state) != 0:
            print("uade_stop error")

        libuade.uade_cleanup_state(self.state)

        if libao.ao_close(self.libao_device) != 1:
            print("ao_close error")

        self.state = 0


class MyThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = True

    def run(self):
        debugpy.debug_this_thread()
        self.uade.init_play(self.current_fname)

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

        self.build_gui()

        self.uade = Pyuade()

        self.thread = MyThread()

    def build_gui(self):
        self.load_btn = QtWidgets.QPushButton("Load")
        self.play_btn = QtWidgets.QPushButton("Play")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.list = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.list)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.load_btn)
        h_layout.addWidget(self.play_btn)
        h_layout.addWidget(self.stop_btn)

        layout.addLayout(h_layout)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self.load)
        self.play_btn.clicked.connect(self.play)
        self.stop_btn.clicked.connect(self.stop)

    @QtCore.Slot()
    def load(self):
        fileName = QFileDialog.getOpenFileName(self, caption="Load music file")
        item = QListWidgetItem(str(fileName[0]), self.list)
        # item.
    @QtCore.Slot()
    def play(self):
        # self.uade.play()
        self.thread.uade = self.uade
        self.thread.current_fname = self.list.item(0).text()
        self.thread.start()
        self.thread.running = True

    @QtCore.Slot()
    def stop(self):
        self.thread.running = False
        self.thread.quit()
        # self.thread.wait()
    
    @QtCore.Slot()
    def clicked(self):
        print("click")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
