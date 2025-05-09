import subprocess
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QPushButton
from PyQt5.QtCore import Qt

from movie import Movie

class MovieButton(QPushButton):
    def __init__(self, movie: Movie):
        super().__init__()
        self.setText(movie.name)
        self.movie = movie
        self.clicked.connect(self.open_movie)

    def open_movie(self):
        if self.movie.is_file:
            subprocess.Popen([r"C:/Program Files (x86)/VideoLAN/VLC/vlc.exe", self.movie.path])
        else:
            subprocess.Popen(f'explorer /select,"{self.movie.path}"')
        

class MainGUIWindow(QMainWindow):
    def __init__(self, movie_list):
        super().__init__()
        self.setWindowTitle("Movie Viewer")
        self.setGeometry(100, 100, 1270, 720)
        self.movie_list = movie_list
        self.initUI()

    def initUI(self):
        self.form_layout = QtWidgets.QFormLayout(self)

        self.movie_group_box = QtWidgets.QGroupBox(self)
        self.movie_group_box.setGeometry(0, 0, 800, 600)
        self.movie_group_box.setTitle("Movie List")

        self.movie_buttons = []
        for movie in self.movie_list:
            button = self.create_movie_button(movie)
            self.form_layout.addWidget(button)
        
        self.movie_group_box.setLayout(self.form_layout)

        self.movie_scroll_area = QtWidgets.QScrollArea(self)
        self.movie_scroll_area.setWidgetResizable(True)
        self.movie_scroll_area.setGeometry(235, 60, 800, 600)
        self.movie_scroll_area.setWidget(self.movie_group_box)
    
    def create_movie_button(self, movie):
        button = MovieButton(movie)
        button.setGeometry(0, len(self.movie_buttons) * 50, 800, 50)
        self.movie_buttons.append(button)
        return button