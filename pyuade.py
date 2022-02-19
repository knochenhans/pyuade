import datetime
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
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QListWidgetItem, QMenu, QSizePolicy, QSlider, QStatusBar, QToolBar, QTreeView, QWidget
from PySide6.QtGui import QAction, QIcon, QStandardItem, QStandardItemModel
import debugpy
import configparser
from appdirs import *
from pathlib import Path
from notifypy import Notify

from ctypes_functions import *
from uade import *

uade = Uade()


class PlayerThread(QThread):
    current_filename: str = []
    current_subsong: int = -1

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = False
        self.paused = False

    def run(self):
        debugpy.debug_this_thread()
        uade.prepare_play(self.current_filename, self.current_subsong)

        while self.running:
            if not self.paused:
                try:
                    uade.play_threaded()
                except EOFError:
                    self.running = False
                except Exception:
                    self.running = False

        uade.stop()


# class Playlist:
#     def __init__(self):
#         pass

#     def insert_song():
#         pass


class TREEVIEWCOL(IntEnum):
    FILENAME = 0
    SONGNAME = 1
    DURATION = 2
    PLAYER = 3
    PATH = 4
    SUBSONG = 5


class MyWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setup_gui()

        self.thread = PlayerThread()
        self.appname = "pyuade"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()

        self.read_config()

        uade.song_end.connect(self.item_finished)
        uade.current_bytes_update.connect(self.timeline_update)
        self.timeline.sliderPressed.connect(self.timeline_pressed)
        self.timeline.sliderReleased.connect(self.timeline_released)

        self.current_row: int = 0
        self.current_index: QModelIndex
        self.timeline_tracking: bool = True

        self.current_song = QItemSelectionModel(self.model)

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
        self.load_action = QAction("Load", self)
        self.load_action.setStatusTip("Load")
        self.load_action.triggered.connect(self.load_clicked)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setStatusTip("Quit")
        self.quit_action.triggered.connect(self.quit_clicked)

        self.play_action = QAction(QIcon("play.svg"), "Play", self)
        self.play_action.setStatusTip("Play")
        self.play_action.triggered.connect(self.play_clicked)

        self.stop_action = QAction(QIcon("stop.svg"), "Stop", self)
        self.stop_action.setStatusTip("Stop")
        self.stop_action.triggered.connect(self.stop_clicked)

        self.prev_action = QAction(QIcon("prev.svg"), "Prev", self)
        self.prev_action.setStatusTip("Prev")
        self.prev_action.triggered.connect(self.prev_clicked)

        self.next_action = QAction(QIcon("next.svg"), "Next", self)
        self.next_action.setStatusTip("Next")
        self.next_action.triggered.connect(self.next_clicked)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setStatusTip("Delete")
        self.delete_action.triggered.connect(self.delete_clicked)

        # self.test_action = QAction("Test", self)
        # self.test_action.setStatusTip("Test")
        # self.test_action.triggered.connect(self.test_clicked)

    def setup_toolbar(self):
        toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        toolbar.addAction(self.play_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.prev_action)
        toolbar.addAction(self.next_action)
        # toolbar.addAction(self.test_action)

        self.timeline = QSlider(QtCore.Qt.Horizontal, self)
        self.timeline.setRange(0, 100)
        self.timeline.setFocusPolicy(QtCore.Qt.NoFocus)
        self.timeline.setPageStep(5)
        self.timeline.setTracking(False)
        # timeline.setStyleSheet("QSlider::handle:horizontal {background-color: red;}")

        toolbar.addWidget(self.timeline)

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
        self.setup_toolbar()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def openMenu(self, position):
        menu = QMenu()
        menu.addAction(self.delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def delete_selected_items(self):
        while self.tree.selectionModel().selectedRows(0):
            idx = self.tree.selectionModel().selectedRows(0)[0]

            #TODO: rebuild
            # if idx.row() == self.current_row:
            #     self.current_row = self.tree.indexBelow(
            #         self.current_row)

            self.model.removeRow(idx.row(), idx.parent())

    def keyPressEvent(self, event):
        if self.tree.selectionModel().selectedRows(0):
            if event.key() == QtCore.Qt.Key_Delete:
                self.delete_selected_items()

    # @ QtCore.Slot()
    # def test_clicked(self):
    #     uade.seek(self.timeline.value() * 2)

    @ QtCore.Slot()
    def quit_clicked(self):
        self.stop()
        QCoreApplication.quit()

    @ QtCore.Slot()
    def item_doubleClicked(self, index):
        self.play(self.tree.selectedIndexes()[0].row())

    def play(self, row: int):
        # self.stop()

        if self.thread.running:
            pass
        else:
            filename = self.model.itemFromIndex(
                self.model.index(row, TREEVIEWCOL.PATH)).text()
            subsong = int(self.model.itemFromIndex(
                self.model.index(row, TREEVIEWCOL.SUBSONG)).text())

            self.play_file_thread(filename, subsong)
            self.current_row = row

            notification = Notify()
            notification.title = "Now playing"
            notification.message = filename
            notification.send(block=False)

            # Select playing track

            self.tree.selectionModel().select(self.model.index(self.current_row, 0),
                                              QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

            subsong = self.model.itemFromIndex(self.model.index(
                self.current_row, 0)).data(QtCore.Qt.UserRole)

            self.timeline.setMaximum(subsong.bytes)

            # Set current track (for pausing)
            self.current_song.setCurrentIndex(self.model.index(
                self.current_row, 0), QItemSelectionModel.SelectCurrent)

    def play_file_thread(self, filename: str, subsong: int):
        # Play filename saved in current item
        self.thread.current_filename = filename
        self.thread.current_subsong = subsong
        self.thread.start()
        self.thread.running = True

    def stop(self):
        self.thread.running = False
        self.thread.quit()
        self.thread.wait()
        self.timeline.setSliderPosition(0)

    def play_next_item(self):
        # current_index actually lists all columns, so for now just take the first col
        if self.current_row < self.model.rowCount(self.tree.rootIndex()) - 1:
            self.play(self.current_row + 1)
        else:
            self.stop()

    def play_previous_item(self):
        # current_index actually lists all columns, so for now just take the first col
        if self.current_row > 0:
            self.play(self.current_row - 1)

    def load_song(self, song):
        # Add all subsongs (including main song)

        for s in range(0, len(song.subsongs)):
            tree_rows = [None] * 6

            tree_rows[TREEVIEWCOL.FILENAME] = QStandardItem(
                ntpath.basename(song.filename))
            # Store subsong in filename column for every row for future use
            tree_rows[TREEVIEWCOL.FILENAME].setData(
                song.subsongs[s], QtCore.Qt.UserRole)
            tree_rows[TREEVIEWCOL.SONGNAME] = QStandardItem(song.modulename)
            tree_rows[TREEVIEWCOL.DURATION] = QStandardItem(
                str(datetime.timedelta(seconds=song.subsongs[s].bytes/176400)).split(".")[0])
            tree_rows[TREEVIEWCOL.PLAYER] = QStandardItem(song.playername)
            tree_rows[TREEVIEWCOL.PATH] = QStandardItem(song.filename)
            tree_rows[TREEVIEWCOL.SUBSONG] = QStandardItem(str(s))

            self.model.appendRow(tree_rows)

    def load_file(self, filename):
        self.load_song(uade.scan_song(filename))

    @ QtCore.Slot()
    def timeline_update(self, bytes):
        if self.timeline_tracking:
            self.timeline.setValue(bytes)

    @ QtCore.Slot()
    def timeline_pressed(self):
        self.timeline_tracking = False

    @ QtCore.Slot()
    def timeline_released(self):
        self.timeline_tracking = True
        uade.seek(self.timeline.sliderPosition())

    @ QtCore.Slot()
    def delete_clicked(self):
        self.delete_selected_items()

    @ QtCore.Slot()
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
                # self.load_file(filename)
                self.load_song(uade.scan_song(filename))

            self.config["files"]["last_open_path"] = os.path.dirname(
                os.path.abspath(filename))

    @ QtCore.Slot()
    def play_clicked(self):
        if self.model.rowCount(self.tree.rootIndex()) > 0:
            if self.thread.paused:
                self.thread.paused = False
            else:
                self.thread.paused = True

    @ QtCore.Slot()
    def stop_clicked(self):
        self.stop()

    @ QtCore.Slot()
    def prev_clicked(self):
        self.play_previous_item()

    @ QtCore.Slot()
    def next_clicked(self):
        self.play_next_item()

    @ QtCore.Slot()
    def item_finished(self):
        print("Playing finished")
        self.stop()
        # self.play_next_item()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
