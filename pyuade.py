import datetime
from enum import IntEnum
from genericpath import exists
import glob
import os
import sys
import ntpath
from xml.etree import ElementTree
# import numpy as np
# import sounddevice as sd
# import soundfile as sf
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QCoreApplication, QDirIterator, QEvent, QPoint, QRect, QSize, QThread, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QFileDialog, QHeaderView, QLabel, QLineEdit, QMenu, QProgressDialog, QSlider, QStatusBar, QStyleOption, QSystemTrayIcon, QTabWidget, QTableWidget, QTableWidgetItem, QToolBar, QTreeView, QVBoxLayout, QWidget
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QKeyEvent, QKeySequence, QMouseEvent, QPainter, QPen, QStandardItem, QStandardItemModel
import debugpy
import configparser
from appdirs import *
from pathlib import Path
from notifypy import Notify
import jsonpickle
import hashlib
import webbrowser
import requests
from bs4 import BeautifulSoup
import re

from ctypes_functions import *
from uade import *

uade = Uade()


class SongInfoDialog(QDialog):
    def __init__(self, song: Song):
        super().__init__()

        attributes = {}

        attributes["Author"] = song.song_file.author
        attributes["Filename"] = song.song_file.filename
        attributes["Format"] = song.song_file.formatname
        attributes["Extension"] = song.song_file.ext
        attributes["Size (Bytes)"] = str(song.song_file.modulebytes)
        attributes["md5"] = song.song_file.modulemd5
        attributes["Player"] = song.song_file.playername
        attributes["Player filename"] = song.song_file.playerfname

        self.setWindowTitle("Song info")

        QBtn = QDialogButtonBox.Close

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.rejected.connect(self.close)

        self.layout = QVBoxLayout()
        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        tableWidget = QTableWidget(self)
        tableWidget.setRowCount(len(attributes))
        tableWidget.setColumnCount(2)
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(tableWidget)

        self.setLayout(self.layout)

        for idx, attribute in enumerate(attributes):
            tableWidget.setItem(idx, 0, QTableWidgetItem(attribute))
            tableWidget.setItem(
                idx, 1, QTableWidgetItem(attributes[attribute]))


class PLAYERTHREADSTATUS(Enum):
    PLAYING = 0,
    PAUSED = 1,
    STOPPED = 2


class PlayerThread(QThread):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.status = PLAYERTHREADSTATUS.STOPPED
        self.current_song: Song

    def run(self):
        debugpy.debug_this_thread()
        uade.prepare_play(self.current_song)

        while self.status == PLAYERTHREADSTATUS.PLAYING:
            try:
                if not uade.play_threaded():
                    self.status = PLAYERTHREADSTATUS.STOPPED
            except EOFError:
                self.status = PLAYERTHREADSTATUS.STOPPED
            except Exception:
                self.status = PLAYERTHREADSTATUS.STOPPED

        uade.stop()


class PlaylistTreeView(QTreeView):
    def __init__(self, parent=None):
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect = QtCore.QRect()

        # Currently playing row for this tab
        self.current_row: int = 0

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

# class MyTreeWidget(QTreeWidget, PlaylistTreeView):


class TREEVIEWCOL(IntEnum):
    FILENAME = 0
    SONGNAME = 1
    DURATION = 2
    PLAYER = 3
    PATH = 4
    SUBSONG = 5
    AUTHOR = 6


class PlaylistTabBarEdit(QtWidgets.QLineEdit):
    def __init__(self, parent, rect: QRect) -> None:
        super().__init__(parent)

        self.setGeometry(rect)
        self.textChanged.connect(parent.tabBar().rename)
        self.editingFinished.connect(parent.tabBar().editing_finished)
        self.returnPressed.connect(self.close)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)


class PlaylistTabBar(QtWidgets.QTabBar):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.edit_text = ""
        self.edit_index = 0
        self.setMovable(True)

    @ QtCore.Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @ QtCore.Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)


class PlaylistTab(QtWidgets.QTabWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        tab = PlaylistTabBar(parent)
        self.setTabBar(tab)

        self.tabBarDoubleClicked.connect(self.doubleClicked)

    @ QtCore.Slot()
    def doubleClicked(self, index) -> None:
        self.tabBar().edit_index = index
        edit = PlaylistTabBarEdit(self, self.tabBar().tabRect(index))
        edit.show()
        edit.setFocus()


class MyWidget(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setup_gui()

        self.current_tab = 0

        self.thread = PlayerThread(self)
        self.appname = "pyuade"
        self.appauthor = "Andre Jonas"

        self.config = configparser.ConfigParser()

        self.read_config()

        uade.song_end.connect(self.item_finished)
        uade.current_bytes_update.connect(self.timeline_update)
        self.timeline.sliderPressed.connect(self.timeline_pressed)
        self.timeline.sliderReleased.connect(self.timeline_released)

        self.timeline_tracking: bool = True

        self.current_selection = QItemSelectionModel(
            self.get_current_tab().model())

        # List of loaded song files for saving the playlist
        # self.song_files: list[SongFile] = []

        self.tray = QSystemTrayIcon(QIcon("play.svg"))
        # self.tray.setContextMenu(menu)
        self.tray.show()

        self.setWindowIcon(QIcon("play.svg"))

    def read_config(self) -> None:

        # Read playlists
        # TODO: do this using md5 of song files?

        playlists = glob.glob(user_config_dir(
            self.appname) + "/playlist-*.json")
        playlists.sort()

        for i, pfile in enumerate(playlists):
            with open(pfile, 'r') as playlist:
                playlist: list[Song] = jsonpickle.decode(playlist.read())

            if playlist:
                self.load_tab(str(i))
                self.playlist_tabs.setCurrentIndex(i)

                for p in playlist:
                    self.load_song(p)

        # Read config

        self.config["window"] = {}
        self.config["files"] = {}
        self.config["playlists"] = {}

        if self.config.read(user_config_dir(self.appname) + '/config.ini'):
            self.resize(int(self.config["window"]["width"]),
                        int(self.config["window"]["height"]))

            if self.config.has_option("files", "current_item"):
                current_item_row = int(self.config["files"]["current_item"])

                if current_item_row >= 0 and current_item_row < self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) - 1:
                    self.get_current_tab().current_row = current_item_row

                    self.get_current_tab().selectionModel().select(self.get_current_tab().model().index(self.get_current_tab().current_row, 0),
                                                                   QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

            # Column width

            for c in range(self.get_current_tab().model().columnCount()):
                if self.config.has_option("window", "col" + str(c) + "_width"):
                    self.get_current_tab().header().resizeSection(
                        c, int(self.config["window"]["col" + str(c) + "_width"]))

            # Playlist tab names

            for t in range(self.playlist_tabs.count()):
                if self.config.has_option("playlists", "playlist" + str(t)):
                    self.playlist_tabs.setTabText(
                        t, self.config["playlists"]["playlist" + str(t)])

    def write_config(self) -> None:

        # Write config

        self.config["window"]["width"] = str(self.geometry().width())
        self.config["window"]["height"] = str(self.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        if self.get_current_tab().current_row >= 0:
            self.config["files"]["current_item"] = str(
                self.get_current_tab().current_row)

        for t in range(0, self.playlist_tabs.count()):
            self.config["playlists"]["playlist" +
                                     str(t)] = self.playlist_tabs.tabText(t)

        # Column width

        for c in range(self.get_current_tab().model().columnCount()):
            self.config["window"]["col" + str(c) +
                                  "_width"] = str(self.get_current_tab().columnWidth(c))

        with open(user_config_dir(self.appname) + "/config.ini", "w") as config_file:
            self.config.write(config_file)

        for t in range(0, self.playlist_tabs.count()):
            tab = self.playlist_tabs.widget(t)

            if tab.model().rowCount() > 0:

                # Write playlist (referencing song files)
                # TODO: do this using md5 of song files?

                with open(user_config_dir(self.appname) + "/playlist-" + str(t) + ".json", "w") as playlist:
                    songs: list[Song] = []

                    for r in range(tab.model().rowCount()):
                        song: Song = tab.model().itemFromIndex(
                            tab.model().index(r, 0)).data(QtCore.Qt.UserRole)

                        songs.append(song)

                    if songs:
                        playlist.write(str(jsonpickle.encode(songs)))

    def setup_actions(self) -> None:
        self.load_action = QAction("Load", self)
        self.load_action.setStatusTip("Load")
        self.load_action.setShortcut(QKeySequence("Ctrl+o"))
        self.load_action.triggered.connect(self.load_clicked)

        self.load_folder_action = QAction("Load folder", self)
        self.load_folder_action.setStatusTip("Load folder")
        self.load_folder_action.setShortcut(QKeySequence("Ctrl+Shift+o"))
        self.load_folder_action.triggered.connect(self.load_folder_clicked)

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

        self.modarchive_action = QAction("Modarchive", self)
        self.modarchive_action.setStatusTip("Modarchive")
        self.modarchive_action.triggered.connect(self.scrape_modarchive)

        self.songinfo_action = QAction("Show song info", self)
        self.songinfo_action.setStatusTip("Show song info")
        self.songinfo_action.triggered.connect(self.show_songinfo)

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
        file_menu.addAction(self.load_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)

    def load_tab(self, name: str) -> None:
        tree = PlaylistTreeView()
        model = QStandardItemModel(0, len(TREEVIEWCOL))
        model.setHorizontalHeaderLabels(self.labels)

        tree.setModel(model)

        tree.setSelectionMode(QTreeView.ExtendedSelection)
        tree.setEditTriggers(QAbstractItemView.NoEditTriggers)

        tree.doubleClicked.connect(self.item_double_clicked)
        tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.open_context_menu)

        self.playlist_tabs.addTab(tree, name)

    def setup_gui(self) -> None:
        # Columns

        self.labels: list[str] = []

        for col in TREEVIEWCOL:
            match col:
                case TREEVIEWCOL.FILENAME:
                    self.labels.append("Filename")
                case TREEVIEWCOL.SONGNAME:
                    self.labels.append("Songname")
                case TREEVIEWCOL.DURATION:
                    self.labels.append("Duration")
                case TREEVIEWCOL.PLAYER:
                    self.labels.append("Player")
                case TREEVIEWCOL.PATH:
                    self.labels.append("Path")
                case TREEVIEWCOL.SUBSONG:
                    self.labels.append("Subsong")
                case TREEVIEWCOL.AUTHOR:
                    self.labels.append("Author")

        # Tree

        # self.get_current_tab()s = list[QTreeView]
        # self.models = list[QStandardItemModel]

        # self.get_current_tab() = QtWidgets.QListWidget()

        self.playlist_tabs = PlaylistTab(self)

        # self.load_tab("Tab 1")
        # self.load_tab("Tab 2")

        # self.setCentralWidget(self.get_current_tab())
        self.setCentralWidget(self.playlist_tabs)

        self.setup_actions()
        self.setup_toolbar()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def closeEvent(self, event: QEvent):
        self.write_config()

    def get_current_tab(self) -> PlaylistTreeView:
        return self.playlist_tabs.widget(self.playlist_tabs.tabBar().currentIndex())

    def open_context_menu(self, position: int) -> None:
        # Song context menu

        menu = QMenu()
        menu.addAction(self.delete_action)
        menu.addAction(self.lookup_msm_action)
        menu.addAction(self.lookup_modland_action)
        menu.addAction(self.sort_action)
        menu.addAction(self.modarchive_action)
        menu.addAction(self.songinfo_action)

        menu.exec(self.get_current_tab().viewport().mapToGlobal(position))

    def delete_selected_items(self):
        while self.get_current_tab().selectionModel().selectedRows(0):
            idx: QModelIndex = self.get_current_tab(
            ).selectionModel().selectedRows(0)[0]

            # TODO: rebuild
            # if idx.row() == self.get_current_tab().current_row:
            #     self.get_current_tab().current_row = self.get_current_tab().indexBelow(
            #         self.get_current_tab().current_row)

            self.get_current_tab().model().removeRow(idx.row(), idx.parent())

    def keyPressEvent(self, event: QEvent):
        if self.get_current_tab().selectionModel().selectedRows(0):
            if event.key() == QtCore.Qt.Key_Delete:
                self.delete_selected_items()

    # @ QtCore.Slot()
    # def test_clicked(self):
    #     uade.seek(self.timeline.value() * 2)

    @ QtCore.Slot()
    def show_songinfo(self) -> None:
        index = self.get_current_tab().selectionModel().selectedRows(0)[0]

        row = index.row()

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(QtCore.Qt.UserRole)

        dialog = SongInfoDialog(song)
        dialog.setWindowTitle(f"Song info for {song.song_file.filename}")
        dialog.resize(700, 300)
        dialog.exec()

    @ QtCore.Slot()
    def scrape_modarchive(self) -> None:
        indexes = self.get_current_tab().selectionModel().selectedRows(0)

        for index in indexes:

            row = index.row()

            song: Song = self.get_current_tab().model().itemFromIndex(
                self.get_current_tab().model().index(row, 0)).data(QtCore.Qt.UserRole)

            license = Path(user_config_dir(
                self.appname) + "/modarchive-api.key")

            if license.exists():
                with open(license, 'r') as f:
                    api_key = f.read()

                    md5 = hashlib.md5()

                    print(
                        f"Looking up {song.song_file.filename} in ModArchive.")

                    with open(song.song_file.filename, 'rb') as f:
                        data = f.read()

                        if data:
                            md5.update(data)

                            md5_request = "request=search&type=hash&query=" + md5.hexdigest()

                            query = f"https://modarchive.org/data/xml-tools.php?key={api_key}&{md5_request}"

                            response = requests.get(query)

                            xml_tree = ElementTree.fromstring(response.content)

                            xml_module = xml_tree.find("module")

                            if xml_module:
                                if int(xml_tree.find("results").text) > 0:
                                    print(
                                        f"ModArchive Metadata found for {song.song_file.filename}.")
                                    xml_artist_info = xml_module.find(
                                        "artist_info")

                                    for artist_idx in range(int(xml_artist_info.find("artists").text)):
                                        xml_artist = xml_artist_info.find(
                                            "artist")

                                        song.song_file.author = xml_artist.find(
                                            "alias").text

                                        print(
                                            f"Artist {song.song_file.author} found for {song.song_file.filename}.")

                                else:
                                    print(
                                        f"More than 1 results for md5 of {song.song_file.filename} found!")

                            else:
                                print(
                                    f"No ModArchive results found for {song.song_file.filename}!")
            else:
                print(f"No modarchive-api.key found in config folder!")

    @ QtCore.Slot()
    def scrape_modland(self, song: Song, column: str) -> str:
        md5 = hashlib.md5()

        with open(song.song_file.filename, 'rb') as f:
            data = f.read()

            if data:
                md5.update(data)

                url = "https://www.exotica.org.uk/mediawiki/index.php?title=Special%3AModland&md=qsearch&qs=" + md5.hexdigest()

                response = requests.get(url)
                if response.status_code == 200:
                    website = requests.get(url)
                    results = BeautifulSoup(website.content, 'html5lib')

                    table = results.find('table', id="ml_resultstable")
                    if table:
                        search_results = table.find('caption')

                        pattern = re.compile(
                            "^Search - ([0-9]+) result.*?$")
                        match = pattern.match(search_results.text)
                        if match:
                            if int(match.group(1)) > 0:
                                # webbrowser.open(url, new=2)
                                table_body = table.find('tbody')

                                author_col_nr = -1

                                # Find out which row contains author (just to make a little more flexible)

                                table_rows = table_body.find_all('tr')
                                for table_row in table_rows:
                                    cols = table_row.find_all('th')

                                    for c, col in enumerate(cols):
                                        header_name = col.find("a")

                                        if header_name.text.strip() == column:
                                            author_col_nr = c
                                            break

                                    if author_col_nr >= 0:
                                        tds = table_row.find_all('td')

                                        if tds:
                                            td = tds[author_col_nr]
                                            return td.find("a").text.strip()
        return ""

    @ QtCore.Slot()
    def lookup_modland_clicked(self):
        # Experimental lookup in modland database

        indexes = self.get_current_tab().selectionModel().selectedRows(0)

        for index in indexes:

            row = index.row()

            song: Song = self.get_current_tab().model().itemFromIndex(
                self.get_current_tab().model().index(row, 0)).data(QtCore.Qt.UserRole)

            song.song_file.author = self.scrape_modland(song, "Author(s)")

            self.get_current_tab().model().itemFromIndex(self.get_current_tab().model().index(
                row, TREEVIEWCOL.AUTHOR)).setText(song.song_file.author)

    @ QtCore.Slot()
    def lookup_msm_clicked(self):
        # Experimental lookup in .Mod Sample Master database
        row = self.get_current_tab().selectedIndexes()[0].row()

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(QtCore.Qt.UserRole)

        sha1 = hashlib.sha1()

        with open(song.song_file.filename, 'rb') as f:
            data = f.read()

            if data:
                sha1.update(data)

                url = "https://modsamplemaster.thegang.nu/module.php?sha1=" + sha1.hexdigest()

                response = requests.get(url)
                if response.status_code == 200:
                    website = requests.get(url)
                    results = BeautifulSoup(website.content, 'html5lib')

                    page = results.find('div', class_='page')
                    if page:
                        name = page.find('h1')

                        if name.text:
                            webbrowser.open(url, new=2)

    @ QtCore.Slot()
    def quit_clicked(self):
        self.stop(False)
        self.thread.wait()
        QCoreApplication.quit()

    @ QtCore.Slot()

    @ QtCore.Slot()
    def item_double_clicked(self, index: QModelIndex):
        self.play(self.get_current_tab().selectedIndexes()[0].row())

    def play(self, row: int):
        if self.thread.status == PLAYERTHREADSTATUS.PLAYING:
            self.stop(False)

        # Get song from user data in column

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(QtCore.Qt.UserRole)

        self.play_file_thread(song)
        self.get_current_tab().current_row = row

        # Select playing track

        self.get_current_tab().selectionModel().select(self.get_current_tab().model().index(self.get_current_tab().current_row, 0),
                                                       QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

        self.timeline.setMaximum(song.subsong.bytes)
        self.time_total.setText(str(datetime.timedelta(
            seconds=song.subsong.bytes/176400)).split(".")[0])

        # Set current song (for pausing)

        self.current_selection.setCurrentIndex(self.get_current_tab().model().index(
            self.get_current_tab().current_row, 0), QItemSelectionModel.SelectCurrent)
        self.thread.current_song = song

        # Notification

        notification = Notify()
        notification.title = "Now playing"
        notification.message = song.song_file.filename
        notification.icon = "play.svg"
        notification.send(block=False)

        print("Now playing " + song.song_file.filename)
        self.tray.setToolTip(f"Playing {song.song_file.filename}")

        self.play_action.setIcon(QIcon("pause.svg"))
        self.load_action.setEnabled(False)

        self.setWindowTitle("pyuade - " + song.song_file.modulename +
                            " - " + song.song_file.filename)

    def play_file_thread(self, song: Song) -> None:
        self.thread.current_song = song
        self.thread.start()
        self.thread.status = PLAYERTHREADSTATUS.PLAYING

    def stop(self, pause_thread: bool) -> None:
        if pause_thread:
            self.thread.status = PLAYERTHREADSTATUS.PAUSED
        else:
            self.thread.status = PLAYERTHREADSTATUS.STOPPED
            self.timeline.setSliderPosition(0)
            self.time.setText("00:00")
            self.time_total.setText("00:00")
            self.setWindowTitle("pyuade")
        self.thread.quit()
        self.thread.wait()
        self.play_action.setIcon(QIcon("play.svg"))
        self.load_action.setEnabled(True)

    def play_next_item(self) -> None:

        index = self.current_selection.currentIndex()

        row = index.row()

        # current_index actually lists all columns, so for now just take the first col
        if row < self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) - 1:
            self.play(row + 1)

    def play_previous_item(self) -> None:
        # current_index actually lists all columns, so for now just take the first col
        if self.get_current_tab().current_row > 0:
            self.play(self.get_current_tab().current_row - 1)

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
                case TREEVIEWCOL.AUTHOR:
                    tree_rows.append(QStandardItem(song.song_file.author))

        self.get_current_tab().model().appendRow(tree_rows)

    def load_file(self, filename: str) -> None:
        try:
            song_file = uade.scan_song_file(filename)
        except:
            print(f"Loading {filename} failed, song skipped")
        else:
            # self.song_files.append(song_file)

            subsongs = uade.split_subsongs(song_file)

            for subsong in subsongs:
                self.load_song(subsong)

    @ QtCore.Slot()
    def timeline_update(self, bytes: int) -> None:
        if self.thread.status == PLAYERTHREADSTATUS.PLAYING:
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
    def load_folder_clicked(self):
        if not self.thread.status == PLAYERTHREADSTATUS.PLAYING:
            if self.config.has_option("files", "last_open_path"):
                last_open_path = self.config["files"]["last_open_path"]

                dir = QFileDialog.getExistingDirectory(
                    self, ("Open music folder"), last_open_path, QFileDialog.ShowDirsOnly)

                # os.getcwd()

                it = QDirIterator(
                    dir, QDirIterator.Subdirectories | QDirIterator.FollowSymlinks)

                while it.hasNext():
                    print(it.next())

                # QDirIterator it(dir, QStringList() << "*.jpg", QDir::Files, QDirIterator::Subdirectories);
                # while (it.hasNext())
                    # qDebug() << it.next();

    @ QtCore.Slot()
    def load_clicked(self):
        if not self.thread.status == PLAYERTHREADSTATUS.PLAYING:
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
        if self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) > 0:
            match self.thread.status:
                case PLAYERTHREADSTATUS.PLAYING:
                    # Play -> pause
                    self.stop(True)
                case PLAYERTHREADSTATUS.PAUSED:
                    # Pause -> play
                    self.play(self.get_current_tab().current_row)
                    uade.seek(self.timeline.sliderPosition())
                    self.play_action.setIcon(QIcon("pause.svg"))
                case (PLAYERTHREADSTATUS.PAUSED | PLAYERTHREADSTATUS.STOPPED):
                    # Play when stopped or paused
                    self.play(self.get_current_tab().current_row)

    @ QtCore.Slot()
    def stop_clicked(self):
        self.stop(False)

    @ QtCore.Slot()
    def prev_clicked(self):
        self.play_previous_item()

    @ QtCore.Slot()
    def next_clicked(self):
        self.play_next_item()

    @ QtCore.Slot()
    def item_finished(self):
        print(f"End of {self.thread.current_song.song_file.filename} reached")
        self.stop(False)
        self.play_next_item()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
