import configparser
import datetime
import glob
import hashlib
import ntpath
import os
import re
import webbrowser
from pathlib import Path
from xml.etree import ElementTree

import jsonpickle
import requests
from appdirs import *
from bs4 import BeautifulSoup
from notifypy import Notify
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import (QCoreApplication, QDirIterator, QEvent,
                            QItemSelectionModel, QModelIndex, QSize, Qt)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (QFileDialog, QLabel, QMenu, QProgressDialog,
                               QSlider, QStatusBar, QSystemTrayIcon, QToolBar)

from ctypes_functions import *
from playerthread import PLAYERTHREADSTATUS, PlayerThread
from playlist import (PlaylistExport, PlaylistItem, PlaylistModel, PlaylistTab,
                      PlaylistTreeView)
from songinfodialog import SongInfoDialog
from uade import Song, uade
from util import TREEVIEWCOL, path


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setup_gui()

        self.current_tab = 0

        self.playerthread = PlayerThread(self)
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

        self.play_icon = QIcon(path + "/play.png")

        self.tray = QSystemTrayIcon(self.play_icon)
        # self.tray.setContextMenu(menu)
        self.tray.show()

        self.setWindowIcon(QIcon(path + "/play.png"))
        self.setAcceptDrops(True)

        self.playlist_tabs.addtabButton.clicked.connect(self.new_tab)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            filenames = []

            for url in event.mimeData().urls():
                filenames.append(url.toLocalFile())

            self.scan_and_load_files(filenames)

    def load_playlist_as_tab(self, filename: str):
        if os.stat(filename).st_size != 0:
            with open(filename, 'r') as playlist_file:
                playlist_export = jsonpickle.decode(playlist_file.read())

                if isinstance(playlist_export, PlaylistExport):
                    if playlist_export.songs:
                        tree = self.add_tab(playlist_export.name)

                        for song in playlist_export.songs:
                            self.load_song(song, tree)

    def read_config(self) -> None:

        # Read config

        self.config["window"] = {}
        self.config["files"] = {}

        if self.config.read(user_config_dir(self.appname) + '/config.ini'):
            self.resize(int(self.config["window"]["width"]),
                        int(self.config["window"]["height"]))

            # Load playlist from files add as tabs
            # TODO: do this using md5 of song files?

            playlist_filenames = glob.glob(user_config_dir(self.appname) + "/playlist-*.json")
            playlist_filenames.sort()

            if len(playlist_filenames) > 0:
                for playlist_filename in playlist_filenames:
                    self.load_playlist_as_tab(playlist_filename)
            else:
                self.add_tab("Default")

            if self.config.has_option("files", "current_item"):
                current_item_row = int(self.config["files"]["current_item"])

                if current_item_row >= 0 and current_item_row < self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) - 1:
                    self.get_current_tab().current_row = current_item_row

                    self.get_current_tab().selectionModel().select(self.get_current_tab().model().index(self.get_current_tab().current_row, 0),
                                                                   QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)

            # Load column width values

            for c in range(self.get_current_tab().model().columnCount()):
                if self.config.has_option("window", "col" + str(c) + "_width"):
                    self.get_current_tab().header().resizeSection(
                        c, int(self.config["window"]["col" + str(c) + "_width"]))

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

        # Column width

        for c in range(self.get_current_tab().model().columnCount()):
            self.config["window"]["col" + str(c) +
                                  "_width"] = str(self.get_current_tab().columnWidth(c))

        with open(user_config_dir(self.appname) + "/config.ini", "w") as config_file:
            self.config.write(config_file)

        # Write playlists (referencing song files)
        # TODO: do this using md5 of song files?

        # Delete existing playlist files
        existing_playlists = glob.glob(user_config_dir(self.appname) + "/playlist-*.json")

        for playlist in existing_playlists:
            os.remove(playlist)

        # Write all tabs as playlists
        for t in range(0, self.playlist_tabs.count()):
            self.write_playlist_file(t)

    def playlist_from_tab(self, tab_nr: int) -> PlaylistExport:
        songs: list[Song] = []

        tab = self.playlist_tabs.widget(tab_nr)

        for row in range(tab.model().rowCount()):
            song: Song = tab.model().itemFromIndex(
                tab.model().index(row, 0)).data(Qt.UserRole)

            songs.append(song)
        tab_name = self.playlist_tabs.tabBar().tabText(tab_nr)
        return PlaylistExport(tab_name, songs)

    def write_playlist_file(self, tab_nr: int) -> None:
        with open(user_config_dir(self.appname) + "/playlist-" + str(tab_nr) + ".json", "w") as playlist:
            playlist.write(str(jsonpickle.encode(self.playlist_from_tab(tab_nr))))

    def setup_gui(self) -> None:
        # Columns

        self.labels: list[str] = []

        for col in TREEVIEWCOL:
            match col:
                case TREEVIEWCOL.PLAYING:
                    self.labels.append("")
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

        self.playlist_tabs = PlaylistTab(self)

        self.setCentralWidget(self.playlist_tabs)

        self.setup_actions()
        self.setup_toolbar()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def setup_actions(self) -> None:
        self.load_action = QAction("Load", self)
        self.load_action.setStatusTip("Load")
        self.load_action.setShortcut(QKeySequence("Ctrl+o"))
        self.load_action.triggered.connect(self.load_clicked)

        self.load_folder_action = QAction("Load folder", self)
        self.load_folder_action.setStatusTip("Load folder")
        self.load_folder_action.setShortcut(QKeySequence("Ctrl+Shift+o"))
        self.load_folder_action.triggered.connect(self.load_folder_clicked)

        self.save_action = QAction("Save", self)
        self.save_action.setStatusTip("Save")
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_action.triggered.connect(self.save_clicked)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setStatusTip("Quit")
        self.quit_action.setShortcut(QKeySequence("Ctrl+q"))
        self.quit_action.triggered.connect(self.quit_clicked)

        self.play_action = QAction(QIcon(path + "/play.png"), "Play", self)
        self.play_action.setStatusTip("Play")
        self.play_action.setShortcut(QKeySequence("p"))
        self.play_action.triggered.connect(self.play_clicked)

        self.stop_action = QAction(QIcon(path + "/stop.png"), "Stop", self)
        self.stop_action.setStatusTip("Stop")
        self.stop_action.setShortcut(QKeySequence("s"))
        self.stop_action.triggered.connect(self.stop_clicked)

        self.prev_action = QAction(QIcon(path + "/prev.png"), "Prev", self)
        self.prev_action.setStatusTip("Prev")
        self.prev_action.setShortcut(QKeySequence("b"))
        self.prev_action.triggered.connect(self.prev_clicked)

        self.next_action = QAction(QIcon(path + "/next.png"), "Next", self)
        self.next_action.setStatusTip("Next")
        self.next_action.setShortcut(QKeySequence("n"))
        self.next_action.triggered.connect(self.next_clicked)

        self.delete_action = QAction("Delete", self)
        self.delete_action.setStatusTip("Delete")
        self.delete_action.triggered.connect(self.delete_clicked)

        self.lookup_msm_action = QAction("Lookup in MSM", self)
        self.lookup_msm_action.setStatusTip("Lookup in MSM")
        self.lookup_msm_action.triggered.connect(self.lookup_msm_clicked)

        self.lookup_modland_action = QAction("Lookup in Modland", self)
        self.lookup_modland_action.setStatusTip("Lookup in Modland")
        self.lookup_modland_action.triggered.connect(
            self.lookup_modland_clicked)

        self.sort_action = QAction("Sort", self)
        self.sort_action.setStatusTip("Sort")
        self.sort_action.triggered.connect(self.sort_clicked)

        self.modarchive_action = QAction("Modarchive", self)
        self.modarchive_action.setStatusTip("Modarchive")
        self.modarchive_action.triggered.connect(self.scrape_modarchive)

        self.songinfo_action = QAction("Show song info", self)
        self.songinfo_action.setStatusTip("Show song info")
        self.songinfo_action.triggered.connect(self.show_songinfo)

        # self.test_action = QAction("Test", self)
        # self.test_action.setStatusTip("Test")
        # self.test_action.triggered.connect(self.test_clicked)

        self.new_tab_action = QAction("New Tab", self)
        self.new_tab_action.setStatusTip("Open a new tab")
        self.new_tab_action.setShortcut(QKeySequence("Ctrl+t"))
        self.new_tab_action.triggered.connect(self.new_tab)

        self.close_tab_action = QAction("Close Tab", self)
        self.close_tab_action.setStatusTip("Close current  tab")
        self.close_tab_action.setShortcut(QKeySequence("Ctrl+w"))
        self.close_tab_action.triggered.connect(self.close_current_tab)

    def setup_toolbar(self) -> None:
        toolbar: QToolBar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        toolbar.addAction(self.play_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.prev_action)
        toolbar.addAction(self.next_action)
        # toolbar.addAction(self.test_action)

        self.timeline = QSlider(Qt.Horizontal, self)
        self.timeline.setRange(0, 100)
        self.timeline.setFocusPolicy(Qt.NoFocus)
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
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)
        edit_menu.addAction(self.new_tab_action)
        edit_menu.addAction(self.close_tab_action)

    def add_tab(self, name: str = '') -> PlaylistTreeView:
        tree = PlaylistTreeView(self)
        model = PlaylistModel(0, len(TREEVIEWCOL))
        model.setHorizontalHeaderLabels(self.labels)

        tree.setModel(model)

        tree.doubleClicked.connect(self.item_double_clicked)
        tree.customContextMenuRequested.connect(self.open_context_menu)

        self.playlist_tabs.addTab(tree, name)
        return tree

    def new_tab(self) -> None:
        self.playlist_tabs.setCurrentWidget(self.add_tab('New Tab'))

    def close_current_tab(self) -> None:
        self.playlist_tabs.remove_current_tab()

    def set_play_status(self, row: int, enable: bool):
        col = self.get_current_tab().model().itemFromIndex(self.get_current_tab().model().index(row, 0))

        if enable:
            col.setData(self.play_icon, Qt.DecorationRole)
        else:
            col.setData(QIcon(), Qt.DecorationRole)

    def load_song(self, song: Song, tab=None) -> None:
        # Add subsong to playlist

        tree_cols: list[PlaylistItem] = []

        for col in TREEVIEWCOL:
            item = PlaylistItem()

            # Store song data in first column
            if col == 0:
                item.setData(song, Qt.UserRole)

            match col:
                case TREEVIEWCOL.PLAYING:
                    item.setText('')
                    #item.setData(QIcon(path + "/play.png"), Qt.DecorationRole)
                case TREEVIEWCOL.FILENAME:
                    item.setText(ntpath.basename(song.song_file.filename))
                case TREEVIEWCOL.SONGNAME:
                    item.setText(song.song_file.modulename)
                case TREEVIEWCOL.DURATION:
                    item.setText(str(datetime.timedelta(seconds=song.subsong.bytes/176400)).split(".")[0])
                case TREEVIEWCOL.PLAYER:
                    item.setText(song.song_file.playername)
                case TREEVIEWCOL.PATH:
                    item.setText(song.song_file.filename)
                case TREEVIEWCOL.SUBSONG:
                    item.setText(str(song.subsong.nr))
                case TREEVIEWCOL.AUTHOR:
                    item.setText(song.song_file.author)

            tree_cols.append(item)

        if not tab:
            tab = self.get_current_tab()

        tab.model().appendRow(tree_cols)

    def load_file(self, filename: str) -> None:
        try:
            song_file = uade.scan_song_file(filename)
        except:
            print(f"Loading {filename} failed, song skipped")
        else:
            # self.song_files.append(song_file)

            subsongs = uade.split_subsongs(song_file)

            # Scrape metadata

            # subsongs[0] = self.scrape_modland(subsongs[0], "Author(s)")

            for subsong in subsongs:
                self.load_song(subsong)

    def scan_and_load_folder(self, dir) -> bool:
        it = QDirIterator(
            dir, QDirIterator.Subdirectories | QDirIterator.FollowSymlinks)

        filenames = []

        while it.hasNext():
            filename = it.next()
            if ntpath.basename(filename) not in ['.', '..']:
                filenames.append(filename)

        if filenames:
            filenames.sort()
            return self.scan_and_load_files(filenames)
        return False

    def scan_and_load_files(self, filenames: list) -> bool:
        filename: str = ""

        if len(filenames) > 0:
            progress = QProgressDialog(
                "Scanning files...", "Cancel", 0, len(filenames), self)
            progress.setWindowModality(Qt.WindowModal)

            for i, filename in enumerate(filenames):
                if os.path.isdir(filename):
                    self.scan_and_load_folder(filename)
                else:
                    progress.setValue(i)
                    if progress.wasCanceled():
                        break

                    self.load_file(filename)

            progress.setValue(len(filenames))
            return True
        return False

    def closeEvent(self, event: QEvent):
        self.write_config()

    def get_current_tab(self) -> PlaylistTreeView:
        return self.playlist_tabs.widget(self.playlist_tabs.tabBar().currentIndex())

    def get_current_tab_index(self) -> int:
        return self.playlist_tabs.tabBar().currentIndex()

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
            if event.key() == Qt.Key_Delete:
                self.delete_selected_items()

    # @ QtCore.Slot()
    # def columnResized(self, logicalIndex: int, oldSize: int, newSize: int) -> None:
    #     print("test")

    # @ QtCore.Slot()
    # def test_clicked(self):
    #     uade.seek(self.timeline.value() * 2)

    @ QtCore.Slot()
    def show_songinfo(self) -> None:
        index = self.get_current_tab().selectionModel().selectedRows(0)[0]

        row = index.row()

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(Qt.UserRole)

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
                self.get_current_tab().model().index(row, 0)).data(Qt.UserRole)

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
                                    print(f"ModArchive Metadata found for {song.song_file.filename}.")
                                    xml_artist_info = xml_module.find(
                                        "artist_info")

                                    for artist_idx in range(int(xml_artist_info.find("artists").text)):
                                        xml_artist = xml_artist_info.find("artist")

                                        song.song_file.author = xml_artist.find("alias").text

                                        print(f"Artist {song.song_file.author} found for {song.song_file.filename}.")

                                else:
                                    print(f"More than 1 results for md5 of {song.song_file.filename} found!")

                            else:
                                print(f"No ModArchive results found for {song.song_file.filename}!")
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
                self.get_current_tab().model().index(row, 0)).data(Qt.UserRole)

            song.song_file.author = self.scrape_modland(song, "Author(s)")

            self.get_current_tab().model().itemFromIndex(self.get_current_tab().model().index(
                row, TREEVIEWCOL.AUTHOR)).setText(song.song_file.author)

    @ QtCore.Slot()
    def lookup_msm_clicked(self):
        # Experimental lookup in .Mod Sample Master database
        row = self.get_current_tab().selectedIndexes()[0].row()

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(Qt.UserRole)

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
        self.playerthread.wait()
        QCoreApplication.quit()

    @ QtCore.Slot()
    def sort_clicked(self):
        indexes = self.get_current_tab().selectedIndexes()

        # print(indexes[0].row())

        # self.get_current_tab().model().moveRow(self.0, 1)

        # indexes.sort(key=lambda x: x., reverse=True)
        pass

    @ QtCore.Slot()
    def item_double_clicked(self, index: QModelIndex):
        # TODO: why [0].row()?
        self.play(self.get_current_tab().selectedIndexes()[0].row())

    def play(self, row: int):
        if self.playerthread.status == PLAYERTHREADSTATUS.PLAYING:
            self.stop(False)

        # Get song from user data in column

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(Qt.UserRole)

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
        self.playerthread.current_song = song

        # Notification

        notification = Notify()
        notification.title = "Now playing"
        notification.message = ""
        if song.song_file.author:
            notification.message += song.song_file.author + " — "
        if song.song_file.modulename:
            notification.message += song.song_file.modulename + " — "
        notification.message += song.song_file.filename
        notification.icon = path + "/play.png"
        notification.send(block=False)

        print("Now playing " + song.song_file.filename)
        self.tray.setToolTip(f"Playing {song.song_file.filename}")

        self.play_action.setIcon(QIcon(path + "/pause.png"))
        self.load_action.setEnabled(False)

        self.setWindowTitle("pyuade - " + song.song_file.modulename +
                            " - " + song.song_file.filename)

        self.set_play_status(row, True)

    def play_file_thread(self, song: Song) -> None:
        self.playerthread.current_song = song
        self.playerthread.start()
        self.playerthread.status = PLAYERTHREADSTATUS.PLAYING

    def stop(self, pause_thread: bool) -> None:
        if pause_thread:
            self.playerthread.status = PLAYERTHREADSTATUS.PAUSED
        else:
            self.playerthread.status = PLAYERTHREADSTATUS.STOPPED
            self.timeline.setSliderPosition(0)
            self.time.setText("00:00")
            self.time_total.setText("00:00")
            self.setWindowTitle("pyuade")
        self.playerthread.quit()
        self.playerthread.wait()
        self.play_action.setIcon(QIcon(path + "/play.png"))
        self.load_action.setEnabled(True)

        index = self.current_selection.currentIndex()

        row = index.row()

        self.set_play_status(row, False)

    def play_next_item(self) -> None:
        index = self.current_selection.currentIndex()

        row = index.row()

        # current_index actually lists all columns, so for now just take the first col
        if row < self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) - 1:
            self.set_play_status(row, False)
            self.play(row + 1)

    def play_previous_item(self) -> None:
        index = self.current_selection.currentIndex()

        row = index.row()

        # current_index actually lists all columns, so for now just take the first col
        if self.get_current_tab().current_row > 0:
            self.set_play_status(row, False)
            self.play(row - 1)

    @ QtCore.Slot()
    def timeline_update(self, bytes: int) -> None:
        if self.playerthread.status == PLAYERTHREADSTATUS.PLAYING:
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
        if not self.playerthread.status == PLAYERTHREADSTATUS.PLAYING:
            if self.config.has_option("files", "last_open_path"):
                last_open_path = self.config["files"]["last_open_path"]

                dir = QFileDialog.getExistingDirectory(
                    self, ("Open music folder"), last_open_path, QFileDialog.ShowDirsOnly)

                if self.scan_and_load_folder(dir):
                    self.config["files"]["last_open_path"] = os.path.dirname(os.path.abspath(dir))

    @ QtCore.Slot()
    def load_clicked(self):
        if not self.playerthread.status == PLAYERTHREADSTATUS.PLAYING:
            if self.config.has_option("files", "last_open_path"):
                last_open_path = self.config["files"]["last_open_path"]

                filenames, filter = QFileDialog.getOpenFileNames(
                    self, caption="Load music file", dir=last_open_path)
            else:
                filenames, filter = QFileDialog.getOpenFileNames(
                    self, caption="Load music file")

            if filenames:
                if self.scan_and_load_files(filenames):
                    self.config["files"]["last_open_path"] = os.path.dirname(
                        os.path.abspath(filenames[0]))

    @ QtCore.Slot()
    def save_clicked(self):
        current_tab = self.get_current_tab_index()

        if current_tab >= 0:
            self.write_playlist_file(current_tab)
            # tab = self.playlist_tabs.widget(current_tab)

            # with open(user_config_dir(self.appname) + "/playlist-" + str(current_tab) + ".json", "w") as playlist:
            #     songs: list[Song] = []

            #     for r in range(tab.model().rowCount()):
            #         song: Song = tab.model().itemFromIndex(
            #             tab.model().index(r, 0)).data(Qt.UserRole)

            #         songs.append(song)

            #     if songs:
            #         playlist.write(str(jsonpickle.encode(songs)))

    @ QtCore.Slot()
    def play_clicked(self):
        if self.get_current_tab().model().rowCount(self.get_current_tab().rootIndex()) > 0:
            match self.playerthread.status:
                case PLAYERTHREADSTATUS.PLAYING:
                    # Play -> pause
                    self.stop(True)
                case PLAYERTHREADSTATUS.PAUSED:
                    # Pause -> play
                    self.play(self.get_current_tab().current_row)
                    uade.seek(self.timeline.sliderPosition())
                    self.play_action.setIcon(QIcon(path + "/pause.png"))
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
        print(f"End of {self.playerthread.current_song.song_file.filename} reached")
        self.stop(False)
        self.play_next_item()
