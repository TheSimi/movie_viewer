import os
from PyQt5.QtWidgets import QApplication

from movie import Movie
from window import MainGUIWindow

def get_movies_in_folder(folder: str):
    movie_list = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            movie_list.append(file_path)
        elif os.path.isdir(file_path):
            if file.startswith('-'):
                movie_list.append(file_path)
            else:
                movie_list.extend(
                    get_movies_in_folder(file_path)
                )
    return movie_list

def get_movie_list():
    with open('path.txt', 'r') as file:
        path = file.read()
        folder_list = path.split('\n')
    movie_path_list = []
    for folder in folder_list:
        movie_path_list.extend(get_movies_in_folder(folder))
    movie_list = []
    for movie in movie_path_list:
        movie_list.append(Movie(movie))
    return movie_list

def main():
    movie_list = get_movie_list()
    
    app = QApplication([])
    win = MainGUIWindow(movie_list)
    win.show()
    app.exec_()

if __name__ == "__main__":
    main()