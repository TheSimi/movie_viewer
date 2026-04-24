import json
import os

import qt_material as qm
from PyQt6.QtWidgets import QApplication

from components.main_window import MainGUIWindow
from const import CONFIG_PATH, DEFAULT_CONFIG, MOVIE_FOLDERS, SHOW_FOLDERS
from services.logger import logger
from utils.cache_utilis import cache_version_handler


def main():
    # setup config.json file and cache folder
    if not os.path.exists(CONFIG_PATH):
        logger.debug(
            f"Could not find config.json at {CONFIG_PATH}. Creating a new one with default values."
        )
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
    cache_version_handler()

    # start the application
    app = QApplication([])
    qm.apply_stylesheet(app, theme="dark_purple.xml")

    win = MainGUIWindow(movie_folders=MOVIE_FOLDERS, show_folders=SHOW_FOLDERS)
    win.showMaximized()

    app.exec()


if __name__ == "__main__":
    main()
