import configparser
import datetime
import glob
import hashlib
import ntpath
import os
import re
import resource
import webbrowser
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import jsonpickle
import requests
from appdirs import user_config_dir
from bs4 import BeautifulSoup
from pynotifier import Notification, NotificationClient
from pynotifier.backends import platform
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import (QCoreApplication, QEvent, QItemSelectionModel,
                            QModelIndex, QSize, Qt)
from PySide6.QtGui import QAction, QIcon, QIntValidator, QKeySequence
from PySide6.QtWidgets import (QFileDialog, QLabel, QMenu, QProgressDialog,
                               QSlider, QStatusBar, QSystemTrayIcon, QToolBar)

from ctypes_functions import *
from loader_thread import LoaderThread
from player_thread import PLAYERTHREADSTATUS, PlayerThread
from playlist import (PlaylistExport, PlaylistItem, PlaylistModel, PlaylistTab,
                      PlaylistTreeView)
from song_info_dialog import SongInfoDialog
from uade import Song, uade
from util import TREEVIEWCOL, path


class OptionsGeneral(QtWidgets.QWidget):
    def __init__(self, parent, settings: QtCore.QSettings):
        super().__init__(parent)

        self.settings = settings

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        hbox = QtWidgets.QHBoxLayout()
        layout.addLayout(hbox)

        buffer = self.settings.value('buffer', 8192)
        self.buffer_edit = QtWidgets.QLineEdit(str(buffer), self)
        self.buffer_edit.setValidator(QIntValidator(0, 1000000, self))

        label = QtWidgets.QLabel('Buffer:', self)
        label.setBuddy(self.buffer_edit)

        hbox.addWidget(label)
        hbox.addWidget(self.buffer_edit)
        hbox.addStretch()


class Options(QtWidgets.QDialog):
    def __init__(self, parent, settings: QtCore.QSettings):
        super().__init__(parent)

        self.tab_widget = QtWidgets.QTabWidget()

        self.general = OptionsGeneral(self, settings)

        self.setWindowTitle(self.tr('Options', 'dialog_options'))

        self.tab_widget.addTab(self.general, 'General')
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        self.layout().addWidget(self.tab_widget)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout().addWidget(self.buttons)


class MainWindow(QtWidgets.QMainWindow):
    appname = "pyuade"
    appauthor = "Andre Jonas"
    config = configparser.ConfigParser()
    settings = QtCore.QSettings('Andre Jonas', 'pyuade')

    def __init__(self) -> None:
        super().__init__()

        self.setup_gui()

        self.current_tab = 0
        self.current_row = 0

        self.player_thread = PlayerThread(self)
        self.loader_thread = LoaderThread(self)

        uade.song_end.connect(self.item_finished)
        uade.current_seconds_update.connect(self.timeline_update_seconds)
        self.timeline.sliderPressed.connect(self.timeline_pressed)
        self.timeline.sliderReleased.connect(self.timeline_released)

        self.timeline_tracking: bool = True

        self.read_config()

        self.current_selection = self.get_current_tab().selectionModel()

        # List of loaded song files for saving the playlist
        # self.song_files: list[SongFile] = []

        self.play_icon = QIcon(os.path.join(path, 'play.png'))

        self.tray = QSystemTrayIcon(self.play_icon, parent=self)
        # self.tray.setContextMenu(menu)
        self.tray.show()

        self.setWindowIcon(QIcon(os.path.join(path, 'play.png')))
        self.setAcceptDrops(True)

        self.playlist_tabs.addtabButton.clicked.connect(self.new_tab)

    def filenames_from_paths(self, paths: list[str]) -> list[str]:
        file_paths = []

        def explore_directory(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    file_paths.append(os.path.join(root, file))

        for path in paths:
            if os.path.isfile(path):
                file_paths.append(path)
            elif os.path.isdir(path):
                explore_directory(path)

        return file_paths

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            filenames = [url.toLocalFile() for url in event.mimeData().urls()]
            self.scan_and_load_files(filenames)

    def load_playlist_as_tab(self, filename: str) -> None:
        try:
            if os.stat(filename).st_size != 0:
                with open(filename, 'r') as playlist_file:
                    playlist_export = jsonpickle.decode(playlist_file.read())

                    if isinstance(playlist_export, PlaylistExport):
                        tree = self.add_tab(playlist_export.name)

                        if playlist_export.songs:
                            for song in playlist_export.songs:
                                self.load_song(song, tree)
            else:
                raise Exception('Playlist file is empty.')
        except FileNotFoundError as e:
            raise Exception(f'Error while reading playlist file: {str(e)}')

    def read_config(self) -> None:
        self.config['window'] = {}
        self.config['files'] = {}

        self.config.read(os.path.join(user_config_dir(self.appname), 'config.ini'))
        window_config = self.config['window']
        files_config = self.config['files']

        self.resize(int(window_config.get('width', '800')),
                    int(window_config.get('height', '600')))

        # Load playlist from files add as tabs
        # TODO: do this using md5 of song files?

        playlist_filenames = glob.glob(os.path.join(user_config_dir(self.appname), 'playlist-*.json'))
        playlist_filenames.sort()

        if len(playlist_filenames) > 0:
            for playlist_filename in playlist_filenames:
                try:
                    self.load_playlist_as_tab(playlist_filename)
                except Exception as e:
                    print(f'Error while loading playlist {playlist_filename}: {e}')
                    self.add_tab('Default')
        else:
            self.add_tab('Default')

        current_item_row = int(files_config.get('current_item', '0'))

        current_tab = self.get_current_tab()

        if current_tab:
            index = current_tab.model().index(current_item_row, 0)
            if index.isValid():
                current_tab.current_row = current_item_row
                current_tab.selectionModel().select(index, QItemSelectionModel.SelectionFlag.SelectCurrent | QItemSelectionModel.SelectionFlag.Rows)

            # Load column width values

            for c in range(current_tab.model().columnCount()):
                current_tab.header().resizeSection(c, int(window_config.get(f'col{str(c)}_width', '100')))

    def write_config(self) -> None:
        window_config = self.config['window']
        files_config = self.config['files']

        window_config = self.config['window']
        files_config = self.config['files']

        window_config['width'] = str(self.geometry().width())
        window_config['height'] = str(self.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        current_tab = self.get_current_tab()
        if current_tab:
            if current_tab.current_row >= 0:
                files_config['current_item'] = str(current_tab.current_row)

            # Column width

            for c in range(current_tab.model().columnCount()):
                window_config[f'col{str(c)}_width'] = str(current_tab.columnWidth(c))

        with open(os.path.join(user_config_dir(self.appname), 'config.ini'), 'w') as config_file:
            self.config.write(config_file)

        # Write playlists (referencing song files)
        # TODO: do this using md5 of song files?

        # Delete existing playlist files
        existing_playlists = glob.glob(os.path.join(user_config_dir(self.appname), 'playlist-*.json'))

        for playlist in existing_playlists:
            os.remove(playlist)

        # Write all tabs as playlists
        for t in range(0, self.playlist_tabs.count()):
            self.write_playlist_file(t)

    def playlist_from_tab(self, tab_nr: int) -> PlaylistExport:
        songs: list[Song] = []

        tab = self.playlist_tabs.widget(tab_nr)
        tab_name = 'Unnamed Tab'

        if isinstance(tab, PlaylistTreeView):
            for row in range(tab.model().rowCount()):
                song: Song = tab.model().itemFromIndex(tab.model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

                songs.append(song)
            tab_name = self.playlist_tabs.tabBar().tabText(tab_nr)
        return PlaylistExport(tab_name, songs)

    def write_playlist_file(self, tab_nr: int) -> None:
        with open(os.path.join(user_config_dir(self.appname), 'playlist-' + str(tab_nr) + '.json'), 'w') as playlist:
            playlist.write(str(jsonpickle.encode(self.playlist_from_tab(tab_nr))))

    def setup_gui(self) -> None:
        # Columns

        self.labels: list[str] = []

        for col in TREEVIEWCOL:
            match col:
                case TREEVIEWCOL.PLAYING:
                    self.labels.append('')
                case TREEVIEWCOL.FILENAME:
                    self.labels.append('Filename')
                case TREEVIEWCOL.SONGNAME:
                    self.labels.append('Songname')
                case TREEVIEWCOL.DURATION:
                    self.labels.append('Duration')
                case TREEVIEWCOL.PLAYER:
                    self.labels.append('Player')
                case TREEVIEWCOL.PATH:
                    self.labels.append('Path')
                case TREEVIEWCOL.SUBSONG:
                    self.labels.append('Subsong')
                case TREEVIEWCOL.AUTHOR:
                    self.labels.append('Author')

        # Tree

        self.playlist_tabs = PlaylistTab(self)

        self.setCentralWidget(self.playlist_tabs)

        self.setup_actions()
        self.setup_toolbar()
        self.setup_menu()

        self.setStatusBar(QStatusBar(self))

    def setup_actions(self) -> None:
        self.load_action = QAction('Load', self)
        self.load_action.setStatusTip('Load')
        self.load_action.setShortcut(QKeySequence('Ctrl+o'))
        self.load_action.triggered.connect(self.load_clicked)

        self.load_folder_action = QAction('Load folder', self)
        self.load_folder_action.setStatusTip('Load folder')
        self.load_folder_action.setShortcut(QKeySequence('Ctrl+Shift+o'))
        self.load_folder_action.triggered.connect(self.load_folder_clicked)

        self.save_action = QAction('Save', self)
        self.save_action.setStatusTip('Save')
        self.save_action.setShortcut(QKeySequence('Ctrl+S'))
        self.save_action.triggered.connect(self.save_clicked)

        self.quit_action = QAction('Quit', self)
        self.quit_action.setStatusTip('Quit')
        self.quit_action.setShortcut(QKeySequence('Ctrl+q'))
        self.quit_action.triggered.connect(self.quit_clicked)

        self.play_action = QAction(QIcon(os.path.join(path, 'play.png')), 'Play', self)
        self.play_action.setStatusTip('Play')
        self.play_action.setShortcut(QKeySequence("p"))
        self.play_action.triggered.connect(self.play_clicked)

        self.stop_action = QAction(QIcon(os.path.join(path, 'stop.png')), 'Stop', self)
        self.stop_action.setStatusTip('Stop')
        self.stop_action.setShortcut(QKeySequence('s'))
        self.stop_action.triggered.connect(self.stop_clicked)

        self.prev_action = QAction(QIcon(os.path.join(path, 'prev.png')), 'Prev', self)
        self.prev_action.setStatusTip('Prev')
        self.prev_action.setShortcut(QKeySequence("b"))
        self.prev_action.triggered.connect(self.prev_clicked)

        self.next_action = QAction(QIcon(os.path.join(path, 'next.png')), 'Next', self)
        self.next_action.setStatusTip('Next')
        self.next_action.setShortcut(QKeySequence('n'))
        self.next_action.triggered.connect(self.next_clicked)

        self.delete_action = QAction('Delete', self)
        self.delete_action.setStatusTip('Delete')
        self.delete_action.triggered.connect(self.delete_clicked)

        self.lookup_msm_action = QAction('Lookup in MSM', self)
        self.lookup_msm_action.setStatusTip('Lookup in MSM')
        self.lookup_msm_action.triggered.connect(self.lookup_msm_clicked)

        self.lookup_modland_action = QAction('Lookup in Modland', self)
        self.lookup_modland_action.setStatusTip('Lookup in Modland')
        self.lookup_modland_action.triggered.connect(self.lookup_modland_clicked)

        self.sort_action = QAction('Sort', self)
        self.sort_action.setStatusTip('Sort')
        self.sort_action.triggered.connect(self.sort_clicked)

        self.modarchive_action = QAction('Modarchive', self)
        self.modarchive_action.setStatusTip('Modarchive')
        self.modarchive_action.triggered.connect(self.scrape_modarchive)

        self.songinfo_action = QAction('Show song info', self)
        self.songinfo_action.setStatusTip('Show song info')
        self.songinfo_action.triggered.connect(self.show_song_info)

        # self.test_action = QAction("Test", self)
        # self.test_action.setStatusTip("Test")
        # self.test_action.triggered.connect(self.test_clicked)

        self.new_tab_action = QAction('New Tab', self)
        self.new_tab_action.setStatusTip('Open a new tab')
        self.new_tab_action.setShortcut(QKeySequence("Ctrl+t"))
        self.new_tab_action.triggered.connect(self.new_tab)

        self.close_tab_action = QAction('Close Tab', self)
        self.close_tab_action.setStatusTip('Close current  tab')
        self.close_tab_action.setShortcut(QKeySequence('Ctrl+w'))
        self.close_tab_action.triggered.connect(self.close_current_tab)

        self.open_options_action = QAction('Options', self)
        self.open_options_action.setShortcut(QKeySequence('Ctrl+P'))
        self.open_options_action.triggered.connect(self.open_options)

    def open_options(self):
        options = Options(self, self.settings)

        if options.exec():
            return True
        else:
            return False

    def setup_toolbar(self) -> None:
        toolbar: QToolBar = QToolBar('Toolbar')
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        toolbar.addAction(self.play_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.prev_action)
        toolbar.addAction(self.next_action)
        # toolbar.addAction(self.test_action)

        self.timeline = QSlider(Qt.Orientation.Horizontal, self)
        self.timeline.setRange(0, 100)
        self.timeline.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.timeline.setPageStep(5)
        self.timeline.setTracking(False)
        # timeline.setStyleSheet("QSlider::handle:horizontal {background-color: red;}")
        toolbar.addWidget(self.timeline)

        self.time = QLabel('00:00')
        self.time_total = QLabel('00:00')
        toolbar.addWidget(self.time)
        toolbar.addWidget(QLabel(' / '))
        toolbar.addWidget(self.time_total)

    def setup_menu(self) -> None:
        menu = self.menuBar()

        file_menu: QMenu = menu.addMenu('&File')
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.load_folder_action)
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()
        file_menu.addAction(self.open_options_action)

        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu('&Edit')
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

    def set_play_status(self, row: int, enable: bool) -> None:
        current_tab = self.get_current_tab()
        if current_tab:
            col = current_tab.model().itemFromIndex(current_tab.model().index(row, 0))

            if enable:
                col.setData(self.play_icon, Qt.ItemDataRole.DecorationRole)
            else:
                col.setData(QIcon(), Qt.ItemDataRole.DecorationRole)

    def load_song(self, song: Song, tab=None) -> None:
        # Add subsong to playlist

        tree_cols: list[PlaylistItem] = []

        if hasattr(song, 'subsong'):
            duration = datetime.timedelta(seconds=song.subsong.bytes/176400)
            subsong_nr = song.subsong.nr
        else:
            duration = datetime.timedelta(seconds=song.song_file.duration)
            subsong_nr = 1

        for col in TREEVIEWCOL:
            item = PlaylistItem()

            # Store song data in first column
            if col == 0:
                item.setData(song, Qt.ItemDataRole.UserRole)

            match col:
                case TREEVIEWCOL.PLAYING:
                    item.setText('')
                    # item.setData(QIcon(path + "/play.png"), Qt.DecorationRole)
                case TREEVIEWCOL.FILENAME:
                    item.setText(ntpath.basename(song.song_file.filename))
                case TREEVIEWCOL.SONGNAME:
                    item.setText(song.song_file.modulename)
                case TREEVIEWCOL.DURATION:
                    item.setText(str(duration).split('.')[0])
                case TREEVIEWCOL.PLAYER:
                    item.setText(song.song_file.playername)
                case TREEVIEWCOL.PATH:
                    item.setText(song.song_file.filename)
                case TREEVIEWCOL.SUBSONG:
                    item.setText(str(subsong_nr))
                case TREEVIEWCOL.AUTHOR:
                    item.setText(song.song_file.author)

            tree_cols.append(item)

        if not tab:
            tab = self.get_current_tab()

        if tab:
            tab.model().appendRow(tree_cols)


    def load_file(self, filename: str) -> None:
        try:
            song_file = uade.scan_song_file(filename)
        except:
            print(f'Loading {filename.encode("utf-8", "surrogateescape").decode("ISO-8859-1")} failed, song skipped')
        else:
            print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            # self.song_files.append(song_file)

            subsongs = uade.split_subsongs(song_file)

            # Scrape metadata

            # subsongs[0] = self.scrape_modland(subsongs[0], "Author(s)")

            for subsong in subsongs:
                self.load_song(subsong)

    def scan_and_load_folder(self, dir) -> bool:
        filenames = sorted([str(p) for p in Path(dir).rglob('*') if p.is_file()], key=lambda x: x.lower())

        if filenames:
            # filenames.sort()
            return self.scan_and_load_files(filenames)
        return False

    def scan_and_load_files(self, filenames: list[str]) -> bool:
        if len(filenames) == 0:
            return False

        filenames = self.filenames_from_paths(filenames)
        filenames.sort(key=lambda x: x.lower())

        self.loader_thread.filenames = filenames
        self.loader_thread.start()
        return True

    def closeEvent(self, event: QEvent):
        self.write_config()

    def get_current_tab(self) -> Optional[PlaylistTreeView]:
        # return self.playlist_tabs.widget(self.playlist_tabs.tabBar().currentIndex())
        widget = self.playlist_tabs.currentWidget()

        if isinstance(widget, PlaylistTreeView):
            return widget
        return None

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

        current_tab = self.get_current_tab()
        if current_tab:
            menu.exec(current_tab.viewport().mapToGlobal(position))

    def delete_selected_items(self):
        current_tab = self.get_current_tab()
        if current_tab:
            selection_model = current_tab.selectionModel()
            selected_rows = selection_model.selectedRows(0)

            # Build a list of row indices to remove
            rows_to_remove = [idx.row() for idx in selected_rows]

            # Sort the row indices in reverse order to maintain correct removal order
            rows_to_remove.sort(reverse=True)

            # Remove the rows from the model
            for row in rows_to_remove:
                current_tab.model().removeRows(row, 1, QModelIndex())

    def keyPressEvent(self, event: QEvent):
        current_tab = self.get_current_tab()
        if current_tab:
            if current_tab.selectionModel().selectedRows(0):
                if event.key() == Qt.Key.Key_Delete:
                    self.delete_selected_items()

    # @ QtCore.Slot()
    # def columnResized(self, logicalIndex: int, oldSize: int, newSize: int) -> None:
    #     print("test")

    # @ QtCore.Slot()
    # def test_clicked(self):
    #     uade.seek(self.timeline.value() * 2)

    @ QtCore.Slot()
    def show_song_info(self) -> None:
        current_tab = self.get_current_tab()
        if current_tab:
            index = current_tab.selectionModel().selectedRows(0)[0]

            row = index.row()

            song: Song = current_tab.model().itemFromIndex(current_tab.model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

            dialog = SongInfoDialog(song)
            dialog.setWindowTitle(f'Song info for {song.song_file.filename}')
            dialog.resize(700, 300)
            dialog.exec()

    @ QtCore.Slot()
    def scrape_modarchive(self) -> None:
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        indexes = current_tab.selectionModel().selectedRows(0)
        license_file = Path(user_config_dir(self.appname)) / 'modarchive-api.key'

        if not license_file.exists():
            print('No modarchive-api.key found in config folder!')
            return

        with open(license_file, 'r') as f:
            api_key = f.read()

        with requests.Session() as session:
            for index in indexes:
                row = index.row()
                song: Song = current_tab.model().itemFromIndex(current_tab.model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

                md5 = hashlib.md5()

                print(f'Looking up {song.song_file.filename} in ModArchive.')

                with open(song.song_file.filename, 'rb') as f:
                    data = f.read()

                    if data:
                        md5.update(data)

                        md5_request = f'request=search&type=hash&query={md5.hexdigest()}'

                        query = f'https://modarchive.org/data/xml-tools.php?key={api_key}&{md5_request}'

                        response = session.get(query)

                        xml_tree = ElementTree.fromstring(response.content)

                        xml_module = xml_tree.find('module')

                        if xml_module:
                            if int(xml_tree.find('results').text) > 0:
                                print(f'ModArchive Metadata found for {song.song_file.filename}.')
                                xml_artist_info = xml_module.find('artist_info')

                                for artist_idx in range(int(xml_artist_info.find('artists').text)):
                                    xml_artist = xml_artist_info.find('artist')

                                    song.song_file.author = xml_artist.find('alias').text

                                    print(f'Artist {song.song_file.author} found for {song.song_file.filename}.')

                            else:
                                print(f'More than 1 results for md5 of {song.song_file.filename} found!')

                        else:
                            print(f'No ModArchive results found for {song.song_file.filename}!')

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
        # Experimental lookup in modland database via MSM

        indexes = self.get_current_tab().selectionModel().selectedRows(0)

        for index in indexes:

            row = index.row()

            song: Song = self.get_current_tab().model().itemFromIndex(
                self.get_current_tab().model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

            # song.song_file.author = self.scrape_modland(song, "Author(s)")
            # Get MSM data
            data = self.scrape_msm(song)

            # Check for url containing modarchive.org
            if 'urls' in data:
                for url in data['urls']:
                    if 'modarchive.org' in url:
                        webbrowser.open(url, new=2)
                        break

            # self.get_current_tab().model().itemFromIndex(self.get_current_tab().model().index(
            #     row, TREEVIEWCOL.AUTHOR)).setText(song.song_file.author)
            
    @ QtCore.Slot()
    def scrape_msm(self, song: Song) -> dict:
        # Lookup in .Mod Sample Master database via sha1 and return data
        return_data = {}

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
                        # Check if we have a result
                        name = page.find('h1')

                        if name.text:
                            return_data['name'] = name.text

                            # Find h1 "Links"
                            links = page.find('h1', string='Links')
                            details = links.find_next_sibling('div')

                            if details:
                                # Read all list items
                                list_items = details.find_all('li')

                                urls = []

                                # Loop through all list items and add them to the return_data
                                for item in list_items:
                                    urls.append(item.text)

                                return_data['urls'] = urls

        return return_data

    @ QtCore.Slot()
    def lookup_msm_clicked(self):
        # Experimental lookup in .Mod Sample Master database
        row = self.get_current_tab().selectedIndexes()[0].row()

        song: Song = self.get_current_tab().model().itemFromIndex(
            self.get_current_tab().model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

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
        self.player_thread.wait()
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
        current_tab = self.get_current_tab()
        if current_tab:
            self.play(current_tab.selectedIndexes()[0].row(), False)

    def show_song_notification(self, song: Song):
        notification_title = 'Now playing'

        notification_message = ''
        if song.song_file.author:
            notification_message += song.song_file.author + ' - '
        if song.song_file.modulename:
            notification_message += song.song_file.modulename + ' - '
        notification_message += song.song_file.filename

        notification = Notification(
            title=notification_title,
            message=notification_message,
            icon_path=os.path.join(path, 'play.png')
        )

        c = NotificationClient()
        c.register_backend(platform.Backend())
        c.notify_all(notification)

    def play(self, row: int, continue_: bool = True):
        current_tab = self.get_current_tab()

        if not current_tab:
            return

        # Get song from user data in column
        song: Song = current_tab.model().itemFromIndex(current_tab.model().index(row, 0)).data(Qt.ItemDataRole.UserRole)

        # Stop the player if it's already playing
        if not continue_:
            if self.player_thread.status in (PLAYERTHREADSTATUS.PLAYING, PLAYERTHREADSTATUS.PAUSED):
                self.stop(False)

            self.play_file_thread(song)
            current_tab.current_row = row

            # Select playing track
            current_tab.selectionModel().select(current_tab.model().index(current_tab.current_row, 0), QItemSelectionModel.SelectionFlag.SelectCurrent | QItemSelectionModel.SelectionFlag.Rows)

            # bytes = 0

            # if hasattr(song, 'subsong'):
            #     bytes = song.subsong.bytes
            # else:
            #     bytes = song.song_file.modulebytes

            # Set timeline and duration
            self.timeline.setMaximum(int(song.song_file.duration * 100))
            self.time_total.setText(str(datetime.timedelta(seconds=song.song_file.duration)).split('.')[0])

            # Set current song (for pausing)
            # self.current_selection.setCurrentIndex(current_tab.model().index(current_tab.current_row, 0), QItemSelectionModel.SelectCurrent)
            self.player_thread.current_song = song

            # Show notification
            self.show_song_notification(song)

            print(f'Now playing {song.song_file.filename}')
            self.current_row = row

            # Update UI
            self.tray.setToolTip(f'Playing {song.song_file.filename}')
        else:
            pass

        self.play_action.setIcon(QIcon(os.path.join(path, 'pause.png')))
        self.load_action.setEnabled(False)
        self.setWindowTitle(f'pyuade - {song.song_file.modulename} - {song.song_file.filename}')

        self.set_play_status(row, True)
        self.player_thread.status = PLAYERTHREADSTATUS.PLAYING

    def play_file_thread(self, song: Song) -> None:
        self.player_thread.current_song = song
        self.player_thread.start()
        self.player_thread.status = PLAYERTHREADSTATUS.PLAYING

    def stop(self, pause_thread: bool) -> None:
        if pause_thread:
            self.player_thread.status = PLAYERTHREADSTATUS.PAUSED
        else:
            self.player_thread.status = PLAYERTHREADSTATUS.STOPPED
            self.timeline.setSliderPosition(0)
            self.time.setText('00:00')
            self.time_total.setText('00:00')
            self.setWindowTitle('pyuade')
        self.player_thread.quit()
        self.player_thread.wait()
        self.play_action.setIcon(QIcon(os.path.join(path, 'play.png')))
        self.load_action.setEnabled(True)

        # index = self.current_selection.currentIndex()

        # row = index.row()

        current_tab = self.get_current_tab()

        if current_tab:
            self.set_play_status(current_tab.current_row, False)

    def play_next_item(self) -> None:
        row = self.current_row

        current_tab = self.get_current_tab()
        if current_tab:
            # current_index actually lists all columns, so for now just take the first col
            if row < current_tab.model().rowCount(current_tab.rootIndex()) - 1:
                self.set_play_status(row, False)
                self.play(row + 1, False)

    def play_previous_item(self) -> None:
        index = self.current_selection.currentIndex()

        row = index.row()

        current_tab = self.get_current_tab()
        if current_tab:
            # current_index actually lists all columns, so for now just take the first col
            if current_tab.current_row > 0:
                self.set_play_status(row, False)
                self.play(row - 1, False)

    # @ QtCore.Slot()
    # def timeline_update(self, bytes: int) -> None:
    #     if self.playerthread.status == PLAYERTHREADSTATUS.PLAYING:
    #         if self.timeline_tracking:
    #             self.timeline.setValue(bytes)

    #         self.time.setText(str(datetime.timedelta(
    #             seconds=bytes/176400)).split(".")[0])

    @ QtCore.Slot()
    def timeline_update_seconds(self, seconds: float) -> None:
        if self.player_thread.status == PLAYERTHREADSTATUS.PLAYING:
            if self.timeline_tracking:
                self.timeline.setValue(int(seconds * 100))

            self.time.setText(str(datetime.timedelta(
                seconds=seconds)).split('.')[0])

    @ QtCore.Slot()
    def timeline_pressed(self):
        self.timeline_tracking = False

    @ QtCore.Slot()
    def timeline_released(self):
        self.timeline_tracking = True
        # uade.seek(self.timeline.sliderPosition())
        uade.seek_seconds(self.timeline.sliderPosition() / 100)

    @ QtCore.Slot()
    def delete_clicked(self):
        self.delete_selected_items()

    @ QtCore.Slot()
    def load_folder_clicked(self):
        if self.player_thread.status != PLAYERTHREADSTATUS.PLAYING:
            last_open_path = self.config.get('files', 'last_open_path', fallback='.')
            dir = QFileDialog.getExistingDirectory(
                self, 'Open music folder', last_open_path, QFileDialog.Option.ShowDirsOnly)
            if dir:
                self.scan_and_load_folder(dir)
                self.config.set('files', 'last_open_path', os.path.abspath(dir))

    @ QtCore.Slot()
    def load_clicked(self):
        if not self.player_thread.status == PLAYERTHREADSTATUS.PLAYING:
            if self.config.has_option('files', 'last_open_path'):
                last_open_path = self.config['files']['last_open_path']

                filenames, filter = QFileDialog.getOpenFileNames(
                    self, caption="Load music file", dir=last_open_path)
            else:
                filenames, filter = QFileDialog.getOpenFileNames(
                    self, caption="Load music file")

            if filenames:
                if self.scan_and_load_files(filenames):
                    self.config['files']['last_open_path'] = os.path.dirname(
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
        current_tab = self.get_current_tab()
        if current_tab:
            if current_tab.model().rowCount(current_tab.rootIndex()) > 0:
                match self.player_thread.status:
                    case PLAYERTHREADSTATUS.PLAYING:
                        # Play -> pause
                        self.stop(True)
                    case PLAYERTHREADSTATUS.PAUSED:
                        # Pause -> play
                        self.play(current_tab.current_row)
                        # uade.seek_seconds(self.timeline.sliderPosition() / 100)
                        self.play_action.setIcon(QIcon(path + '/pause.png'))
                    case (PLAYERTHREADSTATUS.STOPPED):
                        self.play(current_tab.current_row, False)

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
        print(f'End of {self.player_thread.current_song.song_file.filename} reached')
        self.stop(False)
        self.play_next_item()
