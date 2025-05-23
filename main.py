import os
from PyQt6.QtWidgets import QApplication

from get_lists import get_file_list, get_movies_in_folder, get_shows_in_folder
from const import MOVIE_FOLDERS, SHOW_FOLDERS, CACHE_DIR, CACHE_VERSION
from media import Movie, Show
from window import MainGUIWindow
from cache_utilis import clear_all_cache

def check_cache() -> bool:
    if not os.path.exists(CACHE_DIR):
        return False
    version_file = os.path.join(CACHE_DIR, "version.txt")
    if not os.path.exists(version_file):
        return False
    with open(version_file, 'r') as f:
        version = f.read().strip()
    return version == CACHE_VERSION

def cache_version_handler() -> None:
    if not check_cache():
        os.makedirs(CACHE_DIR, exist_ok=True)
        clear_all_cache()

        # Update cache version
        version_file = os.path.join(CACHE_DIR, "version.txt")
        with open(version_file, 'w') as f:
            f.write(CACHE_VERSION)

def main():
    cache_version_handler()

    movie_list = get_file_list(MOVIE_FOLDERS, get_movies_in_folder, Movie)
    show_list = get_file_list(SHOW_FOLDERS, get_shows_in_folder, Show)

    app = QApplication([])
    win = MainGUIWindow(movie_list=movie_list, show_list=show_list)
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
