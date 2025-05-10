from PyQt5.QtWidgets import QApplication

from get_lists import get_file_list, get_movies_in_folder, get_shows_in_folder
from const import MOVIE_FOLDERS, SHOW_FOLDERS
from media import Movie, Show
from window import MainGUIWindow

def main():
    movie_list = get_file_list(MOVIE_FOLDERS, get_movies_in_folder, Movie)
    show_list = get_file_list(SHOW_FOLDERS, get_shows_in_folder, Show)
    
    app = QApplication([])
    win = MainGUIWindow(movie_list=movie_list, show_list=show_list)
    win.show()
    app.exec_()

if __name__ == "__main__":
    main()
