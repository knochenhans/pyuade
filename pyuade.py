from enum import IntEnum
from genericpath import exists
import os
import sys
import ntpath
import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QCoreApplication, QObject, QSettings, QSize, QThread, QAbstractItemModel, QModelIndex, QItemSelectionModel, Signal
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QListWidgetItem, QMenu, QStatusBar, QToolBar, QTreeView
from PySide6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel
import debugpy
from uaddef import *
from externallibs import *
import configparser
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
    subsong_data: Subsong


class Pyuade(QObject):
    song_end = Signal()

    def __init__(self):
        super().__init__()
        libao.ao_initialize()

    # Load and scan a song file

    def load_song(self, filename, subsong_data) -> Song:
        self.state = libuade.uade_new_state(None)

        size = c_size_t()
        buf = c_void_p()

        buf = libuade.uade_read_file(
            byref(size), str.encode(filename))

        if not buf:
            raise Exception(
                "uade_read_file: Cannot read file: {}".format(filename))

        ret = libuade.uade_play(str.encode(filename), subsong_data, self.state)

        if ret < 0:
            raise Exception("uade_play: fatal error: {}, ".format(filename))
        elif ret == 0:
            raise Exception(
                "uade_play: file cannot be played: {}, ".format(filename))

        libc.free(buf)

        info = libuade.uade_get_song_info(self.state).contents

        song = Song()

        if info.formatname:
            song.format = info.formatname.decode()
        if info.modulename:
            song.name = info.modulename.decode()
        if info.playername:
            song.player = info.playername.decode()

        # print(f"{filename} - subsongs: cur {info.subsongs.cur} min {info.subsongs.min} max {info.subsongs.max}")

        if info.subsongs:
            subsong_data = Subsong()
            subsong_data.cur = info.subsongs.cur
            subsong_data.min = info.subsongs.min
            subsong_data.max = info.subsongs.max
            # subsong.def_ = info.subsongs.def

            song.subsong_data = subsong_data

        return song

    def init_play(self, filename, subsong):
        print("Start playing")

        self.state = libuade.uade_new_state(None)

        if not self.state:
            raise Exception("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        self.load_song(filename, subsong)
        # libuade.uade_next_subsong(self.state)

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
    current_subsong: int = -1

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = True

    def run(self):
        debugpy.debug_this_thread()
        uade.init_play(self.current_filename, self.current_subsong)

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


class TREEVIEWCOL(IntEnum):
    FILENAME = 0
    SONGNAME = 1
    DURATION = 2
    PLAYER = 3
    PATH = 4
    SUBSONG = 5


class MyWidget(QtWidgets.QMainWindow):
    current_row: QModelIndex
    playing: bool = False

    def next_track(self):
        if self.current_row < self.model.rowCount():
            self.current_row = self.model.index(
                self.current_row + 1, 4)

    def __init__(self):
        super().__init__()

        self.setup_gui()

        self.thread = PlayerThread()
        self.appname = "pyuade"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()
        self.current_row: int = 0

        self.read_config()

        uade.song_end.connect(self.item_finished)

    def read_config(self):
        # Read playlist

        if exists(user_config_dir(self.appname) + '/playlist'):
            with open(user_config_dir(self.appname) + '/playlist', 'r') as playlist:
                for line in playlist:
                    self.load_file(line.rstrip("\n"))

        # Read config

        self.config["window"] = {}
        self.config["files"] = {}

        if self.config.read(user_config_dir(self.appname) + '/config.ini'):
            self.resize(int(self.config["window"]["width"]),
                        int(self.config["window"]["height"]))

            if self.config.has_option("files", "current_item"):
                current_item_row = int(self.config["files"]["current_item"])

                if current_item_row >= 0 and current_item_row < self.model.rowCount(self.tree.rootIndex()) - 1:
                    self.current_row = current_item_row

            # Column width

            for c in range(self.model.columnCount()):
                if self.config.has_option("window", "col" + str(c) + "_width"):
                    self.tree.header().resizeSection(
                        c, int(self.config["window"]["col" + str(c) + "_width"]))

    def write_config(self):
        # Write config

        self.config["window"]["width"] = str(self.geometry().width())
        self.config["window"]["height"] = str(self.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        if self.current_row >= 0:
            self.config["files"]["current_item"] = str(
                self.current_row)

        # Column width

        for c in range(self.model.columnCount()):
            self.config["window"]["col" + str(c) +
                                  "_width"] = str(self.tree.columnWidth(c))

        with open(user_config_dir(self.appname) + '/config.ini', 'w') as configfile:
            self.config.write(configfile)

        # Write playlist

        filenames = []

        for r in range(self.model.rowCount()):
            index = self.model.index(r, 4)
            filenames.append(self.model.data(index))

            # Ignore subsongs, only save one filename per song
            filenames = list(dict.fromkeys(filenames))

        with open(user_config_dir(self.appname) + '/playlist', 'w') as playlist:
            for line in filenames:
                playlist.write(line + "\n")

    def closeEvent(self, event):
        self.write_config()

    def setup_actions(self):
        toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        self.load_action = QAction("Load", self)
        self.load_action.setStatusTip("Load")
        self.load_action.triggered.connect(self.load_clicked)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setStatusTip("Quit")
        self.quit_action.triggered.connect(self.quit_clicked)

        play_action = QAction(QIcon("play.svg"), "Play", self)
        play_action.setStatusTip("Play")
        play_action.triggered.connect(self.play_clicked)
        toolbar.addAction(play_action)

        stop_action = QAction(QIcon("stop.svg"), "Stop", self)
        stop_action.setStatusTip("Stop")
        stop_action.triggered.connect(self.stop_clicked)
        toolbar.addAction(stop_action)

        prev_action = QAction(QIcon("prev.svg"), "Prev", self)
        prev_action.setStatusTip("Prev")
        prev_action.triggered.connect(self.prev_clicked)
        toolbar.addAction(prev_action)

        next_action = QAction(QIcon("next.svg"), "Next", self)
        next_action.setStatusTip("Next")
        next_action.triggered.connect(self.next_clicked)
        toolbar.addAction(next_action)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setStatusTip("Delete")
        self.delete_action.triggered.connect(self.delete_clicked)

    def setup_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_menu.addAction(self.load_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)

    def setup_gui(self):

        # Tree

        self.tree = QtWidgets.QListWidget()

        self.tree = QTreeView()
        self.model = QStandardItemModel(0, 4)

        labels = [None] * 6
        labels[TREEVIEWCOL.FILENAME] = "Filename"
        labels[TREEVIEWCOL.SONGNAME] = "Songname"
        labels[TREEVIEWCOL.DURATION] = "Duration"
        labels[TREEVIEWCOL.PLAYER] = "Player"
        labels[TREEVIEWCOL.PATH] = "Path"
        labels[TREEVIEWCOL.SUBSONG] = "Subsong"

        self.model.setHorizontalHeaderLabels(labels)
        self.tree.setModel(self.model)

        self.setCentralWidget(self.tree)

        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tree.doubleClicked.connect(self.item_doubleClicked)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)

        self.setup_actions()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def openMenu(self, position):
        menu = QMenu()
        menu.addAction(self.delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def delete_selected_items(self):
        while self.tree.selectionModel().selectedRows(0):
            idx = self.tree.selectionModel().selectedRows(0)[0]
            if idx.row() == self.current_row:
                self.current_row = self.tree.indexBelow(
                    self.current_row)

            self.model.removeRow(idx.row(), idx.parent())

    def keyPressEvent(self, event):
        if self.tree.selectionModel().selectedRows(0):
            if event.key() == QtCore.Qt.Key_Delete:
                self.delete_selected_items()

    @QtCore.Slot()
    def quit_clicked(self):
        QCoreApplication.quit()

    @QtCore.Slot()
    def item_doubleClicked(self, index):
        self.play(self.tree.selectedIndexes()[0].row())

    def play(self, row: int):
        self.stop()

        self.play_file_thread(self.model.itemFromIndex(self.model.index(row, TREEVIEWCOL.PATH)).text(
        ), int(self.model.itemFromIndex(self.model.index(row, TREEVIEWCOL.SUBSONG)).text()))
        self.current_row = row

        # Select playing track

        self.tree.selectionModel().select(self.model.index(self.current_row, 0),
                                          QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

    def play_file_thread(self, filename: str, subsong: int):
        # Play filename saved in current item
        self.thread.current_filename = filename
        self.thread.current_subsong = subsong
        self.thread.start()
        self.thread.running = True
        self.playing = True

    def stop(self):
        self.thread.running = False
        self.thread.quit()
        self.thread.wait()

    def play_next_item(self):
        # current_index actually lists all columns, so for now just take the first col
        if self.current_row < self.model.rowCount(self.tree.rootIndex()) - 1:
            self.play(self.current_row + 1)

    def play_previous_item(self):
        # current_index actually lists all columns, so for now just take the first col
        if self.current_row > 0:
            self.play(self.current_row - 1)

    def load_file(self, filename):
        try:
            song = uade.load_song(filename, 0)
        except Exception:
            print("Loading file failed: ", filename)
        else:
            song.filename = filename

            # Add subsongs as playable songs

            subsongs = 1

            if song.subsong_data.max > 1:
                subsongs = song.subsong_data.max

            for subsong in range(song.subsong_data.cur, subsongs + 1):
                tree_rows = [None] * 6

                tree_rows[TREEVIEWCOL.FILENAME] = QStandardItem(
                    ntpath.basename(song.filename))
                tree_rows[TREEVIEWCOL.SONGNAME] = QStandardItem(song.name)
                tree_rows[TREEVIEWCOL.DURATION] = QStandardItem(
                    str(song.duration))
                tree_rows[TREEVIEWCOL.PLAYER] = QStandardItem(song.player)
                tree_rows[TREEVIEWCOL.PATH] = QStandardItem(song.filename)
                tree_rows[TREEVIEWCOL.SUBSONG] = QStandardItem(str(subsong))

                self.model.appendRow(tree_rows)

    @QtCore.Slot()
    def delete_clicked(self):
        self.delete_selected_items()

    @QtCore.Slot()
    def load_clicked(self):
        if self.config.has_option("files", "last_open_path"):
            last_open_path = self.config["files"]["last_open_path"]

            filenames, filter = QFileDialog.getOpenFileNames(
                self, caption="Load music file", dir=last_open_path)
        else:
            filenames, filter = QFileDialog.getOpenFileNames(
                self, caption="Load music file")

        if filenames:
            for filename in filenames:
                self.load_file(filename)

            self.config["files"]["last_open_path"] = os.path.dirname(
                os.path.abspath(filename))

    @QtCore.Slot()
    def play_clicked(self):
        if self.model.rowCount(self.tree.rootIndex()) > 0:
            self.play(self.current_row)

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
    def item_finished(self):
        self.play_next_item()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
