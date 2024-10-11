import configparser
import glob
import os
from pathlib import Path

from loguru import logger
from platformdirs import user_config_dir
from PySide6 import QtCore

from playlist import PlaylistTreeView


class ConfigManager:
    def __init__(self, appname: str, appauthor: str):
        self.appname = appname
        self.appauthor = appauthor
        self.config = configparser.ConfigParser()
        self.settings = QtCore.QSettings(appauthor, appname)

    def read_config(self, main_window) -> None:
        self.config["window"] = {}
        self.config["files"] = {}

        self.config.read(os.path.join(user_config_dir(self.appname), "config.ini"))
        window_config = self.config["window"]
        files_config = self.config["files"]

        main_window.resize(
            int(window_config.get("width", "800")),
            int(window_config.get("height", "600")),
        )

        playlist_filenames = glob.glob(
            os.path.join(user_config_dir(self.appname), "playlist-*.json")
        )
        playlist_filenames.sort()

        if len(playlist_filenames) > 0:
            for playlist_filename in playlist_filenames:
                try:
                    main_window.load_playlist_as_tab(playlist_filename)
                except Exception as e:
                    logger.error(
                        f"{main_window.log_prefix}Error while loading playlist {playlist_filename}: {e}"
                    )
                    main_window.add_tab("Default")
        else:
            main_window.add_tab("Default")

        current_tab_index = int(files_config.get("current_tab", "0"))
        current_item_row = int(files_config.get("current_item", "0"))

        if current_tab_index >= 0:
            main_window.playlist_tabs.setCurrentIndex(current_tab_index)

            for t in range(0, main_window.playlist_tabs.count()):
                current_tab = main_window.playlist_tabs.widget(t)
                if isinstance(current_tab, PlaylistTreeView):
                    for c in range(current_tab.model().columnCount()):
                        config_value = window_config.get(f"col{str(c)}_width")

                        if config_value:
                            if config_value.isnumeric():
                                current_tab.header().resizeSection(c, int(config_value))

            main_window.select_item(current_item_row, True)

    def write_config(self, main_window) -> None:
        window_config = self.config["window"]
        files_config = self.config["files"]

        window_config["width"] = str(main_window.geometry().width())
        window_config["height"] = str(main_window.geometry().height())

        user_config_path = Path(user_config_dir(self.appname))
        if not user_config_path.exists():
            user_config_path.mkdir(parents=True)

        current_tab = main_window.get_current_tab()
        if current_tab:
            if current_tab.current_row >= 0:
                files_config["current_tab"] = str(
                    main_window.playlist_tabs.currentIndex()
                )
                files_config["current_item"] = str(current_tab.current_row)

            for c in range(current_tab.model().columnCount()):
                window_config[f"col{str(c)}_width"] = str(current_tab.columnWidth(c))

        with open(
            os.path.join(user_config_dir(self.appname), "config.ini"), "w"
        ) as config_file:
            self.config.write(config_file)

        existing_playlists = glob.glob(
            os.path.join(user_config_dir(self.appname), "playlist-*.json")
        )

        for playlist in existing_playlists:
            os.remove(playlist)

        for t in range(0, main_window.playlist_tabs.count()):
            main_window.write_playlist_file(t)
