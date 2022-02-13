from ast import For
from genericpath import exists
from logging import exception
import os
import pathlib
from pyexpat import model
import sys
import time
import ntpath
import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, QSettings, QThread, QAbstractItemModel, QModelIndex, QItemSelectionModel, Signal
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QListWidgetItem, QTreeView
from PySide6.QtGui import QStandardItem, QStandardItemModel
import debugpy
from uaddef import *
from externallibs import *
import configparser
import json
from appdirs import *
from pathlib import Path


class Subsong():
    cur: int = 0
    min: int = 0
    max: int = 0
    def_: int = 0


class Song():
    name: str = ""
    filename: str = ""
    duration: int = 0
    player: str = ""
    format: str = ""
    subsongs: Subsong = []


class Pyuade(QObject):
    song_end = Signal()

    def __init__(self):
        super().__init__()
        libao.ao_initialize()

    def load_song(self, fname) -> Song:
        self.state = libuade.uade_new_state(None)

        size = c_size_t()
        buf = c_void_p()

        buf = libuade.uade_read_file(
            byref(size), str.encode(fname))

        if not buf:
            raise Exception(
                "uade_read_file: Cannot read file: {}".format(fname))

        ret = libuade.uade_play(str.encode(fname), -1, self.state)

        if ret < 0:
            raise Exception("uade_play: fatal error: {}, ".format(fname))
        elif ret == 0:
            raise Exception(
                "uade_play: file cannot be played: {}, ".format(fname))

        libc.free(buf)

        info = libuade.uade_get_song_info(self.state).contents

        song = Song()

        if info.formatname:
            song.format = info.formatname.decode()
        if info.modulename:
            song.name = info.modulename.decode()
        if info.playername:
            song.player = info.playername.decode()

        # print(f"subsongs: cur {info.subsongs.cur} min {info.subsongs.min} max {info.subsongs.max}")
        if info.subsongs:
            subsong = Subsong()
            subsong.cur = info.subsongs.cur
            subsong.min = info.subsongs.min
            subsong.max = info.subsongs.max
            # subsong.def_ = info.subsongs.def

        return song

    def init_play(self, filename):
        print("Start playing")

        self.state = libuade.uade_new_state(None)

        if not self.state:
            raise Exception("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        self.load_song(filename)

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
            raise Exception("Playback error")
        elif nbytes == 0:
            self.song_end.emit()
            # raise EOFError("Song end")

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


uade = Pyuade()


class PlayerThread(QThread):
    current_filename: str = []

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = True

    def run(self):
        debugpy.debug_this_thread()
        uade.init_play(self.current_filename)

        while self.running:
            try:
                uade.play()
            except EOFError:
                self.running = False
            except Exception:
                self.running = False

        uade.stop()


class Playlist:
    def __init__(self):
        pass

    def insert_song():
        pass


class MyWidget(QtWidgets.QWidget):
    current_index: QModelIndex
    playing: bool = False

    def next_track(self):
        if self.current_index.row() < self.model.rowCount():
            self.current_index = self.model.index(
                self.current_index.row() + 1, 4)

    def __init__(self):
        super().__init__()

        self.build_gui()

        self.thread = PlayerThread()
        self.appname = "pyuade"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()
        self.current_index = self.model.index(0, 4)

        self.read_config()

        uade.song_end.connect(self.item_finished)

    def read_config(self):
        # Read playlist

        if exists(user_config_dir(self.appname) + '/playlist'):
            with open(user_config_dir(self.appname) + '/playlist', 'r') as playlist:
                for line in playlist:
                    self.load_file(line.rstrip("\n"))

        # Read config

        if self.config.read(user_config_dir(self.appname) + '/config.ini'):
            self.resize(int(self.config["window"]["width"]),
                        int(self.config["window"]["height"]))

            current_item_row = int(self.config["files"]["current_item"])

            if current_item_row >= self.model.rowCount(self.tree.rootIndex()) - 1:
                self.current_index = self.model.index(current_item_row, 4)

    def write_config(self):
        # Write config

        self.config["window"] = {}
        self.config["window"]["width"] = str(self.geometry().width())
        self.config["window"]["height"] = str(self.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        self.config["files"] = {}
        if self.current_index:
            self.config["files"]["current_item"] = str(
                self.current_index.row())

        with open(user_config_dir(self.appname) + '/config.ini', 'w') as configfile:
            self.config.write(configfile)

        # Write playlist

        filenames = []

        for r in range(self.model.rowCount()):
            index = self.model.index(r, 4)
            filenames.append(self.model.data(index))

        if filenames:
            with open(user_config_dir(self.appname) + '/playlist', 'w') as playlist:
                for line in filenames:
                    playlist.write(line + "\n")

    def closeEvent(self, event):
        self.write_config()

    def build_gui(self):
        self.load_btn = QtWidgets.QPushButton("Load")
        self.play_btn = QtWidgets.QPushButton("Play")
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.prev_btn = QtWidgets.QPushButton("Prev")
        self.next_btn = QtWidgets.QPushButton("Next")
        self.tree = QtWidgets.QListWidget()

        self.tree = QTreeView()
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(
            ["Filename", "Songname", "Duration", "Player", "Path"])
        self.tree.setModel(self.model)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tree)

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.load_btn)
        h_layout.addWidget(self.play_btn)
        h_layout.addWidget(self.stop_btn)
        h_layout.addWidget(self.prev_btn)
        h_layout.addWidget(self.next_btn)

        layout.addLayout(h_layout)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self.load_clicked)
        self.play_btn.clicked.connect(self.play_clicked)
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn.clicked.connect(self.next_clicked)

        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tree.doubleClicked.connect(self.item_doubleClicked)

    @QtCore.Slot()
    def item_doubleClicked(self, index):
        self.play(self.tree.selectedIndexes()[4])

    def play(self, index):
        self.stop()

        self.play_file_thread(self.model.itemFromIndex(index).text())
        self.current_index = index

        # Select playing track

        self.tree.selectionModel().select(self.current_index,
                                          QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

    def play_file_thread(self, filename: str):
        # Play filename saved in current item
        self.thread.current_filename = filename
        self.thread.start()
        self.thread.running = True
        self.playing = True

    def stop(self):
        self.thread.running = False
        self.thread.quit()
        self.thread.wait()

    def play_next_item(self):
        if self.current_index.row() < self.model.rowCount(self.tree.rootIndex()) - 1:
            self.play(self.tree.indexBelow(self.current_index))

    def play_previous_item(self):
        if self.current_index.row() > 0:
            self.play(self.tree.indexAbove(self.current_index))

    def load_file(self, filename):
        try:
            song = uade.load_song(filename)
        except Exception:
            print("Loading file failed: ", filename)
        else:
            song.filename = filename
            self.model.appendRow([QStandardItem(ntpath.basename(song.filename)), QStandardItem(
                song.name), QStandardItem(str(song.duration)), QStandardItem(song.player), QStandardItem(song.filename)])

    @QtCore.Slot()
    def load_clicked(self):
        last_open_path = self.config["files"]["last_open_path"]

        filenames, filter = QFileDialog.getOpenFileNames(
            self, caption="Load music file", dir=last_open_path)

        if filenames:
            for filename in filenames:
                self.load_file(filename)

            self.config["files"]["last_open_path"] = os.path.dirname(
                os.path.abspath(filename))

    @QtCore.Slot()
    def play_clicked(self):
        if self.model.rowCount(self.tree.rootIndex()) > 0:
            self.play(self.current_index)

    @QtCore.Slot()
    def stop_clicked(self):
        self.stop()

    @QtCore.Slot()
    def prev_clicked(self):
        self.play_previous_item()

    @QtCore.Slot()
    def next_clicked(self):
        self.play_next_item()

    @QtCore.Slot()
    def clicked(self):
        print("click")

    @QtCore.Slot()
    def item_finished(self):
        self.play_next_item()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
