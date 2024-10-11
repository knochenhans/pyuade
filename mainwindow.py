import configparser
import datetime
import ntpath
import os
import resource
import webbrowser
from pathlib import Path
from typing import Optional

import jsonpickle
import psutil
from appdirs import user_config_dir
from loguru import logger
from pynotifier import Notification, NotificationClient
from pynotifier.backends import platform
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import (QCoreApplication, QEvent, QItemSelectionModel,
                            QModelIndex, QSize, Qt)
from PySide6.QtGui import QAction, QIcon, QKeyEvent, QKeySequence
from PySide6.QtWidgets import (QLabel, QMenu, QSlider, QStatusBar,
                               QSystemTrayIcon, QToolBar)

import configmanager
# from ctypes_functions import *
from audio_backends.pyaudio.audio_backend_pyuadio import AudioBackendPyAudio
from loader_thread import LoaderThread
from options import Options
from player_backends.libopenmpt.player_backend_libopenmpt import \
    PlayerBackendLibOpenMPT
from player_backends.libuade.ctypes_classes import uade_song_info
from player_backends.libuade.player_backend_libuade import PlayerBackendLibUADE
from player_backends.libuade.songinfo import UadeSongInfoType
from player_backends.player_backend import PlayerBackend
from player_thread import PlayerThread
from playlist import (PlaylistExport, PlaylistItem, PlaylistModel, PlaylistTab,
                      PlaylistTreeView)
from scraping import lookup_msm, scrape_modarchive, scrape_modland, scrape_msm
from song_info_dialog import SongInfoDialog
from uade import Song, uade
from util import TREEVIEWCOL, path


class MainWindow(QtWidgets.QMainWindow):
    appname = "pyuade"
    appauthor = "Andre Jonas"
    config = configparser.ConfigParser()
    settings = QtCore.QSettings("Andre Jonas", "pyuade")

    icons: dict[str, QIcon] = {}

    play_signal = QtCore.Signal()

    log_prefix = "[MainWindow] "

    def __init__(self) -> None:
        super().__init__()

        psutil.Process().nice(0)

        self.setup_gui()

        self.player_thread: Optional[PlayerThread] = None
        self.loader_thread = LoaderThread(self)
        self.loader_thread.finished.connect(self.loader_finished)

        self.config_manager = configmanager.ConfigManager(self.appname, self.appauthor)
        self.config_manager.read_config(self)

        self.player_backends = {
            "LibUADE": PlayerBackendLibUADE,
            "LibOpenMPT": PlayerBackendLibOpenMPT,
        }
        self.player_backend: Optional[PlayerBackend]
        self.audio_backend: Optional[AudioBackendPyAudio] = None

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
                with open(filename, "r") as playlist_file:
                    playlist_export = jsonpickle.decode(playlist_file.read())

                    if isinstance(playlist_export, PlaylistExport):
                        tree = self.add_tab(playlist_export.name)

                        if playlist_export.songs:
                            for song in playlist_export.songs:
                                self.load_song(song, tree)
            else:
                raise Exception("Playlist file is empty.")
        except FileNotFoundError as e:
            raise Exception(f"Error while reading playlist file: {str(e)}")

    def playlist_from_tab(self, tab_nr: int) -> PlaylistExport:
        songs: list[Song] = []

        tab = self.playlist_tabs.widget(tab_nr)
        tab_name = "Unnamed Tab"

        current_tab = self.get_current_tab()

        if current_tab:
            model = current_tab.model()

            if isinstance(model, PlaylistModel):
                if isinstance(tab, PlaylistTreeView):
                    for row in range(model.rowCount()):
                        song: Song = model.itemFromIndex(model.index(row, 0)).data(
                            Qt.ItemDataRole.UserRole
                        )

                        songs.append(song)
                    tab_name = self.playlist_tabs.tabBar().tabText(tab_nr)
        return PlaylistExport(tab_name, songs)

    def write_playlist_file(self, tab_nr: int) -> None:
        with open(
            os.path.join(
                user_config_dir(self.appname), "playlist-" + str(tab_nr) + ".json"
            ),
            "w",
        ) as playlist:
            playlist.write(str(jsonpickle.encode(self.playlist_from_tab(tab_nr))))

    def setup_gui(self) -> None:
        self.icon_filenames = {"play", "pause", "stop", "prev", "next"}

        for icon in self.icon_filenames:
            self.icons[icon] = QIcon(os.path.join("images", f"{icon}.png"))

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

        self.current_tab = 0
        self.current_row = 0

        self.timeline_tracking: bool = True

        current_tab = self.get_current_tab()
        self.current_selection: Optional[QItemSelectionModel] = None

        if current_tab:
            self.current_selection = current_tab.selectionModel()
        else:
            # Handle the case when there is no current tab
            self.current_selection = None

        # List of loaded song files for saving the playlist
        # self.song_files: list[SongFile] = []

        self.tray = QSystemTrayIcon(self.icons["play"], parent=self)
        # self.tray.setContextMenu(menu)
        self.tray.show()

        self.setWindowIcon(self.icons["play"])
        self.setAcceptDrops(True)

        self.playlist_tabs.addtabButton.clicked.connect(self.new_tab)

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

        self.play_action = QAction(QIcon(os.path.join("images", "play.png")), "Play", self)
        self.play_action.setStatusTip("Play")
        self.play_action.setShortcut(QKeySequence("p"))
        self.play_action.triggered.connect(self.play_pause_clicked)

        self.stop_action = QAction(QIcon(os.path.join("images", "stop.png")), "Stop", self)
        self.stop_action.setStatusTip("Stop")
        self.stop_action.setShortcut(QKeySequence("s"))
        self.stop_action.triggered.connect(self.stop_clicked)

        self.prev_action = QAction(QIcon(os.path.join("images", "prev.png")), "Prev", self)
        self.prev_action.setStatusTip("Prev")
        self.prev_action.setShortcut(QKeySequence("b"))
        self.prev_action.triggered.connect(self.prev_clicked)

        self.next_action = QAction(QIcon(os.path.join("images", "next.png")), "Next", self)
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
        self.lookup_modland_action.triggered.connect(self.lookup_modland_clicked)

        self.sort_action = QAction("Sort", self)
        self.sort_action.setStatusTip("Sort")
        self.sort_action.triggered.connect(self.sort_clicked)

        self.modarchive_action = QAction("Modarchive", self)
        self.modarchive_action.setStatusTip("Modarchive")
        self.modarchive_action.triggered.connect(self.scrape_modarchive_clicked)

        self.songinfo_action = QAction("Show song info", self)
        self.songinfo_action.setStatusTip("Show song info")
        self.songinfo_action.triggered.connect(self.show_song_info)

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

        self.open_options_action = QAction("Options", self)
        self.open_options_action.setShortcut(QKeySequence("Ctrl+P"))
        self.open_options_action.triggered.connect(self.open_options)

    def open_options(self):
        options = Options(self, self.settings)

        if options.exec():
            return True
        else:
            return False

    def setup_toolbar(self) -> None:
        toolbar: QToolBar = QToolBar("Toolbar")
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
        self.timeline.sliderPressed.connect(self.timeline_pressed)
        self.timeline.sliderReleased.connect(self.timeline_released)
        # timeline.setStyleSheet("QSlider::handle:horizontal {background-color: red;}")
        toolbar.addWidget(self.timeline)

        self.time = QLabel("00:00")
        self.time_total = QLabel("00:00")
        toolbar.addWidget(self.time)
        toolbar.addWidget(QLabel(" / "))
        toolbar.addWidget(self.time_total)

    def select_item(self, row: int, scroll: bool = True) -> None:
        current_tab = self.get_current_tab()

        if current_tab:
            model = current_tab.model()

            if isinstance(model, PlaylistModel):
                index = model.index(row, 0)

                if index.isValid():
                    current_tab.selectionModel().select(
                        index,
                        QItemSelectionModel.SelectionFlag.SelectCurrent
                        | QItemSelectionModel.SelectionFlag.Rows,
                    )

                    if scroll:
                        current_tab.scrollTo(index)

    def setup_menu(self) -> None:
        menu = self.menuBar()

        file_menu: QMenu = menu.addMenu("&File")
        file_menu.addAction(self.load_action)
        file_menu.addAction(self.load_folder_action)
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()
        file_menu.addAction(self.open_options_action)

        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = menu.addMenu("&Edit")
        edit_menu.addAction(self.delete_action)
        edit_menu.addAction(self.new_tab_action)
        edit_menu.addAction(self.close_tab_action)

    def add_tab(self, name: str = "") -> PlaylistTreeView:
        tree = PlaylistTreeView(self)
        model = PlaylistModel(0, len(TREEVIEWCOL))
        model.setHorizontalHeaderLabels(self.labels)

        tree.setModel(model)

        tree.doubleClicked.connect(self.item_double_clicked)
        tree.customContextMenuRequested.connect(self.open_context_menu)

        self.playlist_tabs.addTab(tree, name)
        return tree

    def new_tab(self) -> None:
        self.playlist_tabs.setCurrentWidget(self.add_tab("New Tab"))

    def close_current_tab(self) -> None:
        self.playlist_tabs.remove_current_tab()

    def set_play_status(self, row: int, enable: bool) -> None:
        current_tab = self.get_current_tab()

        if current_tab:
            model = current_tab.model()

            if isinstance(model, PlaylistModel):
                if current_tab:
                    col = model.itemFromIndex(current_tab.model().index(row, 0))

                    if enable:
                        col.setData(self.icons["play"], Qt.ItemDataRole.DecorationRole)
                    else:
                        col.setData(QIcon(), Qt.ItemDataRole.DecorationRole)

    # Add subsong to playlist
    def load_song(self, song: Song, tab=None) -> None:
        tree_cols: list[PlaylistItem] = []

        if hasattr(song, "subsong"):
            duration = datetime.timedelta(seconds=song.subsong.bytes / 176400)
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
                    item.setText("")
                    # item.setData(QIcon(path + "/play.png"), Qt.DecorationRole)
                case TREEVIEWCOL.FILENAME:
                    item.setText(ntpath.basename(song.song_file.filename))
                case TREEVIEWCOL.SONGNAME:
                    item.setText(song.song_file.modulename)
                case TREEVIEWCOL.DURATION:
                    item.setText(str(duration).split(".")[0])
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
            model = tab.model()

            if isinstance(model, PlaylistModel):
                model.appendRow(tree_cols)

    def load_file(self, filename: str) -> None:
        try:
            song_file = uade.scan_song_file(filename)
        except:
            logger.error(
                f'{self.log_prefix}Loading {filename.encode("utf-8", "surrogateescape").decode("ISO-8859-1")} failed, song skipped'
            )
        else:
            print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            # self.song_files.append(song_file)

            subsongs = uade.split_subsongs(song_file)

            # Scrape metadata

            # subsongs[0] = self.scrape_modland(subsongs[0], "Author(s)")

            for subsong in subsongs:
                self.load_song(subsong)

    def scan_and_load_folder(self, dir) -> bool:
        filenames = sorted(
            [str(p) for p in Path(dir).rglob("*") if p.is_file()],
            key=lambda x: x.lower(),
        )

        if filenames:
            # filenames.sort()
            return self.scan_and_load_files(filenames)
        return False

    def scan_and_load_files(self, filenames: list[str]) -> bool:
        if len(filenames) == 0:
            return False

        filenames = self.filenames_from_paths(filenames)
        filenames.sort(key=lambda x: x.lower())

        self.enable_ui(False)

        self.loader_thread.filenames = filenames
        self.loader_thread.start()
        return True

    def closeEvent(self, event: QEvent):
        self.config_manager.write_config(self)

    def get_current_tab(self) -> Optional[PlaylistTreeView]:
        # return self.playlist_tabs.widget(self.playlist_tabs.tabBar().currentIndex())
        widget = self.playlist_tabs.currentWidget()

        if isinstance(widget, PlaylistTreeView):
            return widget
        return None

    def get_current_tab_index(self) -> int:
        return self.playlist_tabs.tabBar().currentIndex()

    def open_context_menu(self, position: QtCore.QPoint) -> None:
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

    def keyPressEvent(self, event: QKeyEvent):
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

    @QtCore.Slot()
    def show_song_info(self) -> None:
        current_tab = self.get_current_tab()
        if current_tab:
            index = current_tab.selectionModel().selectedRows(0)[0]

            row = index.row()

            model = current_tab.model()

            if isinstance(model, PlaylistModel):
                song: Song = model.itemFromIndex(
                    current_tab.model().index(row, 0)
                ).data(Qt.ItemDataRole.UserRole)

                dialog = SongInfoDialog(song)
                dialog.setWindowTitle(f"Song info for {song.song_file.filename}")
                dialog.resize(700, 300)
                dialog.exec()

    def song_from_index(self, index: QModelIndex) -> Song | None:
        current_tab = self.get_current_tab()
        if current_tab:
            model = current_tab.model()

            row = index.row()

            if isinstance(model, PlaylistModel):
                song: Song = model.itemFromIndex(
                    current_tab.model().index(row, 0)
                ).data(Qt.ItemDataRole.UserRole)

                return song
        return None

    def get_selected_songs(self) -> list[Song]:
        songs = []

        current_tab = self.get_current_tab()
        if current_tab:
            indexes = current_tab.selectionModel().selectedRows(0)

            for index in indexes:
                song = self.song_from_index(index)
                if song:
                    songs.append(song)

        return songs

    @QtCore.Slot()
    def scrape_modarchive_clicked(self) -> None:
        songs = self.get_selected_songs()

        updated_songs = []

        if songs:
            for song in songs:
                updated_songs.append(scrape_modarchive(self.appname, song))

    @QtCore.Slot()
    def scrape_modland_clicked(self) -> None:
        songs = self.get_selected_songs()

        updated_songs = []

        if songs:
            for song in songs:
                updated_songs.append(scrape_modland(song, "Author"))

    @QtCore.Slot()
    def lookup_modland_clicked(self):
        # Experimental lookup in modland database via MSM

        # song.song_file.author = self.scrape_modland(song, "Author(s)")
        # Get MSM data
        songs = self.get_selected_songs()

        if len(songs) > 0:
            song = songs[0]
            data = scrape_msm(song)

            # Check for url containing modarchive.org
            if "urls" in data:
                for url in data["urls"]:
                    if "modarchive.org" in url:
                        webbrowser.open(url, new=2)
                        break

            # self.get_current_tab().model().itemFromIndex(self.get_current_tab().model().index(
            #     row, TREEVIEWCOL.AUTHOR)).setText(song.song_file.author)

    @QtCore.Slot()
    def lookup_msm_clicked(self) -> None:
        # Experimental lookup in .Mod Sample Master database
        url = lookup_msm(self.get_selected_songs()[0])

        if url:
            webbrowser.open(url, new=2)

    @QtCore.Slot()
    def quit_clicked(self):
        QCoreApplication.quit()

    @QtCore.Slot()
    def sort_clicked(self):
        current_tab = self.get_current_tab()

        if current_tab:
            indexes = current_tab.selectedIndexes()

        # print(indexes[0].row())

        # self.get_current_tab().model().moveRow(self.0, 1)

        # indexes.sort(key=lambda x: x., reverse=True)
        pass

    @QtCore.Slot()
    def item_double_clicked(self, index: QModelIndex):
        self.stop()
        self.reset_gui()
        # TODO: why [0].row()?
        current_tab = self.get_current_tab()
        if current_tab:
            self.play_at_index(current_tab.selectedIndexes()[0].row())

    def show_song_notification(self, song: Song):
        notification_title = "Now playing"

        notification_message = ""
        if song.song_file.author:
            notification_message += song.song_file.author + " - "
        if song.song_file.modulename:
            notification_message += song.song_file.modulename + " - "
        notification_message += song.song_file.filename

        notification = Notification(
            title=notification_title,
            message=notification_message,
            icon_path=os.path.join("images", "play.png"),
        )

        c = NotificationClient()
        c.register_backend(platform.Backend())
        c.notify_all(notification)

    def find_player(self, filename) -> str:
        # Try to load the module by going through the available player backends
        for backend_name, backend_class in self.player_backends.items():
            logger.debug(f"Trying player backend: {backend_name}")

            player_backend = backend_class()
            if player_backend is not None:
                if player_backend.load_module(filename):
                    self.player_backend = player_backend
                    break

        if self.player_backend is None:
            raise ValueError("No player backend could load the module, skipping")
        logger.debug(f"Module successfully loaded with player backend: {backend_name}")
        return backend_name

    # Play the song at the given row
    def play_at_index(self, row: int):
        if self.player_thread and self.player_thread.isRunning():
            self.player_thread.pause()
            if self.player_thread.pause_flag:
                # self.play_button.setIcon(
                #     self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
                # )
                # self.stop_button.setEnabled(False)
                pass
            else:
                # self.play_button.setIcon(
                #     self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
                # )
                # self.stop_button.setEnabled(True)
                pass
        else:
            current_tab = self.get_current_tab()

            if not current_tab:
                return

            model = current_tab.model()

            song = self.song_from_index(model.index(row, 0))

            if song:
                # self.playManager.play(song)
                backend_name = self.find_player(song.song_file.filename)

                # Set timeline and duration
                self.timeline.setMaximum(int(song.song_file.duration * 100))
                self.time_total.setText(
                    str(datetime.timedelta(seconds=song.song_file.duration)).split(".")[
                        0
                    ]
                )
                # self.playManager.player_thread.current_seconds_update.connect(
                #     self.timeline_update_seconds
                # )
                buffer = self.settings.value("buffer", type=int)

                if not isinstance(buffer, int):
                    buffer = 8192

                samplerate = self.settings.value("samplerate", type=int)

                if not isinstance(samplerate, int):
                    samplerate = 44100

                self.audio_backend = AudioBackendPyAudio(samplerate, buffer)

                if self.player_backend is not None:
                    self.player_thread = PlayerThread(
                        self.player_backend, self.audio_backend
                    )
                    self.player_thread.song_finished.connect(self.next_clicked)
                    self.player_thread.position_changed.connect(
                        self.timeline_update_seconds
                    )
                    self.player_thread.start()

                # Show notification
                self.show_song_notification(song)

                logger.info(f"{self.log_prefix}Now playing {song.song_file.filename}")
                self.current_row = row

                # Update UI
                self.tray.setToolTip(f"Playing {song.song_file.filename}")

                if isinstance(model, PlaylistModel):
                    #         if not continue_:
                    #             self.play_file_thread(song)
                    current_tab.current_row = row

                    # Select playing track
                    current_tab.selectionModel().select(
                        current_tab.model().index(current_tab.current_row, 0),
                        QItemSelectionModel.SelectionFlag.SelectCurrent
                        | QItemSelectionModel.SelectionFlag.Rows,
                    )

                self.set_play_status(row, True)

                #             # bytes = 0

                #             # if hasattr(song, 'subsong'):
                #             #     bytes = song.subsong.bytes
                #             # else:
                #             #     bytes = song.song_file.modulebytes

                #             # Set current song (for pausing)
                #             # self.current_selection.setCurrentIndex(current_tab.model().index(current_tab.current_row, 0), QItemSelectionModel.SelectCurrent)
                #             self.player_thread.current_song = song

                #     else:
                #         pass

                #     self.play_action.setIcon(QIcon(os.path.join(path, "pause.png")))
                #     self.load_action.setEnabled(False)
                #     self.setWindowTitle(
                #         f"pyuade - {song.song_file.modulename} - {song.song_file.filename}"
                #     )

        #     self.player_thread.status = STATUS.PLAYING

    # @QtCore.Slot()
    # def paused(self) -> None:
    #     self.play_action.setIcon(self.icons["pause"])

    def stop(self) -> None:
        if self.player_thread:
            logger.debug("Stopping player thread")
            self.player_thread.stop()
            if not self.player_thread.wait(5000):
                self.player_thread.terminate()
                self.player_thread.wait()

            if self.player_backend:
                self.player_backend.free_module()
            self.audio_backend = None

            # self.play_button.setIcon(
            #     self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            # )
            # self.stop_button.setEnabled(False)
            # self.progress_slider.setEnabled(False)
            logger.debug("Player thread stopped")
        self.reset_gui()

    @QtCore.Slot()
    def reset_gui(self) -> None:
        self.timeline.setSliderPosition(0)
        self.time.setText("00:00")
        self.time_total.setText("00:00")
        self.setWindowTitle(self.appname)

        self.play_action.setIcon(self.icons["play"])
        self.load_action.setEnabled(True)

        # index = self.current_selection.currentIndex()

        # row = index.row()

        current_tab = self.get_current_tab()

        if current_tab:
            self.set_play_status(current_tab.current_row, False)

    @QtCore.Slot()
    def play_pause_clicked(self):
        current_tab = self.get_current_tab()
        if current_tab:
            if current_tab.model().rowCount(current_tab.rootIndex()) > 0:
                self.play_at_index(current_tab.current_row)

    @QtCore.Slot()
    def stop_clicked(self):
        self.stop()

    @QtCore.Slot()
    def prev_clicked(self):
        self.play_next_previous_item(False)

    @QtCore.Slot()
    def next_clicked(self):
        self.play_next_previous_item(True)

    def play_next_previous_item(self, next: bool) -> None:
        self.stop()
        current_tab = self.get_current_tab()
        if current_tab:
            if current_tab.model().rowCount(current_tab.rootIndex()) > 0:
                row = current_tab.current_row

                if next:
                    if row < current_tab.model().rowCount(current_tab.rootIndex()) - 1:
                        self.set_play_status(row, False)
                        self.play_at_index(row + 1)
                else:
                    if row > 0:
                        self.set_play_status(row, False)
                        self.play_at_index(row - 1)

    # @ QtCore.Slot()
    # def timeline_update(self, bytes: int) -> None:
    #     if self.playerthread.status == STATUS.PLAYING:
    #         if self.timeline_tracking:
    #             self.timeline.setValue(bytes)

    #         self.time.setText(str(datetime.timedelta(
    #             seconds=bytes/176400)).split(".")[0])

    @QtCore.Slot()
    def timeline_update_seconds(self, milliseconds: float) -> None:
        if self.timeline_tracking:
            seconds = milliseconds / 1000
            self.timeline.setValue(int(milliseconds / 10))
            self.time.setText(str(datetime.timedelta(seconds=seconds)).split(".")[0])

    @QtCore.Slot()
    def timeline_pressed(self):
        self.timeline_tracking = False

    @QtCore.Slot()
    def timeline_released(self):
        self.timeline_tracking = True
        # uade.seek(self.timeline.sliderPosition())
        uade.seek_seconds(self.timeline.sliderPosition() / 100)

    @QtCore.Slot()
    def delete_clicked(self):
        self.delete_selected_items()

    @QtCore.Slot()
    def load_folder_clicked(self):
        # if self.player_thread.status != STATUS.PLAYING:
        #     last_open_path = self.config.get("files", "last_open_path", fallback=".")
        #     dir = QFileDialog.getExistingDirectory(
        #         self,
        #         "Open music folder",
        #         last_open_path,
        #         QFileDialog.Option.ShowDirsOnly,
        #     )
        #     if dir:
        #         self.scan_and_load_folder(dir)
        #         self.config.set("files", "last_open_path", os.path.abspath(dir))
        pass

    @QtCore.Slot()
    def load_clicked(self):
        # if not self.player_thread.status == STATUS.PLAYING:
        #     if self.config.has_option("files", "last_open_path"):
        #         last_open_path = self.config["files"]["last_open_path"]

        #         filenames, filter = QFileDialog.getOpenFileNames(
        #             self, caption="Load music file", dir=last_open_path
        #         )
        #     else:
        #         filenames, filter = QFileDialog.getOpenFileNames(
        #             self, caption="Load music file"
        #         )

        #     if filenames:
        #         if self.scan_and_load_files(filenames):
        #             self.config["files"]["last_open_path"] = os.path.dirname(
        #                 os.path.abspath(filenames[0])
        #             )
        pass

    @QtCore.Slot()
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

    def enable_ui(self, enable: bool) -> None:
        self.play_action.setEnabled(enable)
        self.stop_action.setEnabled(enable)
        self.prev_action.setEnabled(enable)
        self.next_action.setEnabled(enable)
        self.delete_action.setEnabled(enable)
        self.lookup_msm_action.setEnabled(enable)
        self.lookup_modland_action.setEnabled(enable)
        self.sort_action.setEnabled(enable)
        self.modarchive_action.setEnabled(enable)
        self.songinfo_action.setEnabled(enable)

    @QtCore.Slot()
    def loader_finished(self):
        self.enable_ui(True)
