import dotenv
from PyQt6.QtWidgets import QApplication
import qt_material as qm

from const import MOVIE_FOLDERS, SHOW_FOLDERS
from components.main_window import MainGUIWindow
from utils.cache_utilis import cache_version_handler

def main():
    # setup .env file and cache folder
    if not dotenv.find_dotenv():
        with open('.env', 'w') as f:
            f.write(
                'MOVIE_FOLDERS=""\n'
                'SHOW_FOLDERS=""\n'
                'MEDIA_PLAYER="vlc"\n'
                'SPEED="1"\n'
            )
    cache_version_handler()

    # start the application
    app = QApplication([])
    qm.apply_stylesheet(app, theme='dark_purple.xml')

    win = MainGUIWindow(movie_folders=MOVIE_FOLDERS, show_folders=SHOW_FOLDERS)
    win.showMaximized()

    app.exec()

if __name__ == "__main__":
    main()
