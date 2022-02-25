import datetime
from enum import IntEnum
from genericpath import exists
import os
import sys
import ntpath
# import numpy as np
# import sounddevice as sd
# import soundfile as sf
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QCoreApplication, QEvent, QSize, QThread, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QLabel, QMenu, QProgressDialog, QSlider, QStatusBar, QToolBar, QTreeView
from PySide6.QtGui import QAction, QIcon, QKeySequence, QStandardItem, QStandardItemModel
import debugpy
import configparser
from appdirs import *
from pathlib import Path
from notifypy import Notify
import jsonpickle

from ctypes_functions import *
from uade import *

uade = Uade()


class PlayerThread(QThread):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.running = False
        self.paused = False
        self.current_song: Song

    def run(self):
        debugpy.debug_this_thread()
        uade.prepare_play(self.current_song)

        while self.running:
            if not self.paused:
                try:
                    if not uade.play_threaded():
                        self.running = False
                except EOFError:
                    self.running = False
                except Exception:
                    self.running = False

        uade.stop()


class MyTreeView(QTreeView):
    def __init__(self, parent=None):
        super(MyTreeView, self).__init__(parent)
        self.dropIndicatorRect = QtCore.QRect()

    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        self.drawTree(painter, event.region())
        self.paintDropIndicator(painter)

    def paintDropIndicator(self, painter):

        if self.state() == QAbstractItemView.DraggingState:
            opt = QStyleOption()
            opt.init(self)
            opt.rect = self.dropIndicatorRect
            rect = opt.rect

            brush = QBrush(QColor(QtCore.Qt.black))

            if rect.height() == 0:
                pen = QPen(brush, 2, QtCore.Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                pen = QPen(brush, 2, QtCore.Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)

# class MyTreeWidget(QTreeWidget, MyTreeView):


class TREEVIEWCOL(IntEnum):
    FILENAME = 0
    SONGNAME = 1
    DURATION = 2
    PLAYER = 3
    PATH = 4
    SUBSONG = 5


class MyWidget(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setup_gui()

        self.thread = PlayerThread(self)
        self.appname = "pyuade"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()

        self.read_config()

        uade.song_end.connect(self.item_finished)
        uade.current_bytes_update.connect(self.timeline_update)
        self.timeline.sliderPressed.connect(self.timeline_pressed)
        self.timeline.sliderReleased.connect(self.timeline_released)

        self.current_row: int = 0
        self.timeline_tracking: bool = True

        self.current_selection = QItemSelectionModel(self.model)

        # List of loaded song files for saving the playlist
        # self.song_files: list[SongFile] = []

    def read_config(self) -> None:

        # Read song files and playlist
        # TODO: do this using md5 of song files

        # if exists(user_config_dir(self.appname) + '/songfiles.json'):
        #     with open(user_config_dir(self.appname) + '/songfiles.json', 'r') as playlist:
        #         self.song_files = jsonpickle.decode(playlist.read())

        if exists(user_config_dir(self.appname) + '/playlist.json'):
            with open(user_config_dir(self.appname) + '/playlist.json', 'r') as playlist:
                playlist: list[Song] = jsonpickle.decode(playlist.read())

            if playlist:
                for p in playlist:
                    self.load_song(p)

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

    def write_config(self) -> None:

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

        with open(user_config_dir(self.appname) + '/config.ini', 'w') as config_file:
            self.config.write(config_file)

        if self.model.rowCount() > 0:

            # Write song files

            # if self.song_files:
            #     with open(user_config_dir(self.appname) + '/songfiles.json', 'w') as song_files:
            #         song_files.write(str(jsonpickle.encode(self.song_files)))

            # Write playlist (referencing song files)
            # TODO: do this using md5 of song files

            with open(user_config_dir(self.appname) + '/playlist.json', 'w') as playlist:
                songs: list[Song] = []

                for r in range(self.model.rowCount()):
                    song: Song = self.model.itemFromIndex(
                        self.model.index(r, 0)).data(QtCore.Qt.UserRole)

                    songs.append(song)

                if songs:
                    playlist.write(str(jsonpickle.encode(songs)))

    def setup_actions(self) -> None:
        self.load_action = QAction("Load", self)
        self.load_action.setStatusTip("Load")
        self.load_action.setShortcut(QKeySequence("Ctrl+o"))
        self.load_action.triggered.connect(self.load_clicked)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setStatusTip("Quit")
        self.quit_action.setShortcut(QKeySequence("Ctrl+q"))
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

    def setup_toolbar(self) -> None:
        toolbar: QToolBar = QToolBar("Toolbar")
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

        self.time = QLabel("00:00")
        self.time_total = QLabel("00:00")
        toolbar.addWidget(self.time)
        toolbar.addWidget(QLabel(" / "))
        toolbar.addWidget(self.time_total)

    def setup_menu(self) -> None:
        menu = self.menuBar()

        file_menu: QMenu = menu.addMenu("&File")
        file_menu.addAction(self.load_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)

    def setup_gui(self) -> None:

        # Tree

        self.tree = QtWidgets.QListWidget()

        self.tree = MyTreeView()
        self.model = QStandardItemModel(0, 4)

        labels: list[str] = []

        for col in TREEVIEWCOL:
            match col:
                case TREEVIEWCOL.FILENAME:
                    labels.append("Filename")
                case TREEVIEWCOL.SONGNAME:
                    labels.append("Songname")
                case TREEVIEWCOL.DURATION:
                    labels.append("Duration")
                case TREEVIEWCOL.PLAYER:
                    labels.append("Player")
                case TREEVIEWCOL.PATH:
                    labels.append("Path")
                case TREEVIEWCOL.SUBSONG:
                    labels.append("Subsong")

        self.model.setHorizontalHeaderLabels(labels)
        self.tree.setModel(self.model)

        self.setCentralWidget(self.tree)

        self.tree.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tree.doubleClicked.connect(self.item_double_clicked)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_menu)

        self.setup_actions()
        self.setup_toolbar()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def closeEvent(self, event: QEvent):
        self.write_config()

    def open_menu(self, position: int) -> None:
        menu = QMenu()
        menu.addAction(self.delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def delete_selected_items(self):
        while self.tree.selectionModel().selectedRows(0):
            idx: QModelIndex = self.tree.selectionModel().selectedRows(0)[0]

            # TODO: rebuild
            # if idx.row() == self.current_row:
            #     self.current_row = self.tree.indexBelow(
            #         self.current_row)

            self.model.removeRow(idx.row(), idx.parent())

    def keyPressEvent(self, event: QEvent):
        if self.tree.selectionModel().selectedRows(0):
            if event.key() == QtCore.Qt.Key_Delete:
                self.delete_selected_items()

    # @ QtCore.Slot()
    # def test_clicked(self):
    #     uade.seek(self.timeline.value() * 2)

    @ QtCore.Slot()
    def quit_clicked(self):
        self.stop()
        self.thread.wait()
        QCoreApplication.quit()

    @ QtCore.Slot()
    def item_double_clicked(self, index: QModelIndex):

        self.play(self.tree.selectedIndexes()[0].row())

    def play(self, row: int):
        if self.thread.running:
            self.stop()

        # Get song from user data in column

        song: Song = self.model.itemFromIndex(
            self.model.index(row, 0)).data(QtCore.Qt.UserRole)

        self.play_file_thread(song)
        self.current_row = row

        # Select playing track

        self.tree.selectionModel().select(self.model.index(self.current_row, 0),
                                          QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

        self.timeline.setMaximum(song.subsong.bytes)
        self.time_total.setText(str(datetime.timedelta(
            seconds=song.subsong.bytes/176400)).split(".")[0])

        # Set current song (for pausing)

        self.current_selection.setCurrentIndex(self.model.index(
            self.current_row, 0), QItemSelectionModel.SelectCurrent)
        self.thread.current_song = song

        # Notification

        notification = Notify()
        notification.title = "Now playing"
        notification.message = song.song_file.filename
        notification.icon = "play.svg"
        notification.send(block=False)

        print("Now playing " + song.song_file.filename)

        self.play_action.setIcon(QIcon("pause.svg"))

    def play_file_thread(self, song: Song) -> None:
        self.thread.current_song = song
        self.thread.start()
        self.thread.running = True

    def stop(self) -> None:
        self.thread.running = False
        self.thread.paused = False
        self.thread.quit()
        self.thread.wait()
        self.timeline.setSliderPosition(0)
        self.time.setText("00:00")
        self.time_total.setText("00:00")
        self.play_action.setIcon(QIcon("play.svg"))

    def play_next_item(self) -> None:

        index = self.current_selection.currentIndex()

        row = index.row()

        # current_index actually lists all columns, so for now just take the first col
        if row < self.model.rowCount(self.tree.rootIndex()) - 1:
            self.play(row + 1)

    def play_previous_item(self) -> None:
        # current_index actually lists all columns, so for now just take the first col
        if self.current_row > 0:
            self.play(self.current_row - 1)

    def load_song(self, song: Song) -> None:
        # Add subsong to playlist

        tree_rows: list[QStandardItem] = []

        for col in TREEVIEWCOL:
            match col:
                case TREEVIEWCOL.FILENAME:
                    item = QStandardItem(
                        ntpath.basename(song.song_file.filename))

                    # Store song in filename column for every row for future use
                    item.setData(song, QtCore.Qt.UserRole)
                    tree_rows.append(item)
                case TREEVIEWCOL.SONGNAME:
                    tree_rows.append(QStandardItem(song.song_file.modulename))
                case TREEVIEWCOL.DURATION:
                    tree_rows.append(QStandardItem(str(datetime.timedelta(
                        seconds=song.subsong.bytes/176400)).split(".")[0]))
                case TREEVIEWCOL.PLAYER:
                    tree_rows.append(QStandardItem(song.song_file.playername))
                case TREEVIEWCOL.PATH:
                    tree_rows.append(QStandardItem(song.song_file.filename))
                case TREEVIEWCOL.SUBSONG:
                    tree_rows.append(QStandardItem(str(song.subsong.nr)))

        self.model.appendRow(tree_rows)

    def load_file(self, filename: str) -> None:
        song_file = uade.scan_song_file(filename)
        # self.song_files.append(song_file)

        subsongs = uade.split_subsongs(song_file)

        for subsong in subsongs:
            self.load_song(subsong)

    @ QtCore.Slot()
    def timeline_update(self, bytes: int) -> None:
        if self.timeline_tracking:
            self.timeline.setValue(bytes)

        self.time.setText(str(datetime.timedelta(
            seconds=bytes/176400)).split(".")[0])

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
            filename: str = ""

            progress = QProgressDialog(
                "Scanning files...", "Cancel", 0, len(filenames), self)
            progress.setWindowModality(QtCore.Qt.WindowModal)

            for i, filename in enumerate(filenames):
                progress.setValue(i)
                if progress.wasCanceled():
                    break

                self.load_file(filename)

            progress.setValue(len(filenames))

            self.config["files"]["last_open_path"] = os.path.dirname(
                os.path.abspath(filename))

    @ QtCore.Slot()
    def play_clicked(self):
        if self.model.rowCount(self.tree.rootIndex()) > 0:
            if self.thread.running:
                if self.thread.paused:
                    self.thread.paused = False
                    self.play_action.setIcon(QIcon("pause.svg"))
                else:
                    self.thread.paused = True
                    self.play_action.setIcon(QIcon("play.svg"))
            else:
                self.play(self.current_row)

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
        print(f"End of {self.thread.current_song.song_file.filename} reached")
        self.stop()
        self.play_next_item()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
