from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QPushButton
from PyQt5.QtCore import Qt

from media import Media

class MediaButton(QPushButton):
    def __init__(self, media: Media):
        super().__init__()
        self.setText(media.name)
        self.media = media
        self.clicked.connect(self.media.play)

class MainGUIWindow(QMainWindow):
    def __init__(self, movie_list=None, show_list=None):
        super().__init__()
        self.movie_list = movie_list or []
        self.show_list = show_list or []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Movie Viewer")
        self.setGeometry(100, 100, 1270, 720)

        self.make_movie_scroll_area()
        self.make_show_scroll_area()
    
    def make_show_scroll_area(self):
        self.show_form_layout = QtWidgets.QFormLayout(self)

        self.show_group_box = QtWidgets.QGroupBox(self)
        self.show_group_box.setGeometry(635, 0, 635, 600)
        self.show_group_box.setTitle("Show List")

        self.show_buttons = []
        for show in self.show_list:
            button = self.create_media_button(show)
            self.show_form_layout.addWidget(button)

        self.show_group_box.setLayout(self.show_form_layout)

        self.show_scroll_area = QtWidgets.QScrollArea(self)
        self.show_scroll_area.setWidgetResizable(True)
        self.show_scroll_area.setGeometry(635, 60, 635, 600)
        self.show_scroll_area.setWidget(self.show_group_box)

    def make_movie_scroll_area(self):
        self.movie_form_layout = QtWidgets.QFormLayout(self)

        self.movie_group_box = QtWidgets.QGroupBox(self)
        self.movie_group_box.setGeometry(0, 0, 635, 600)
        self.movie_group_box.setTitle("Movie List")

        self.movie_buttons = []
        for movie in self.movie_list:
            button = self.create_media_button(movie)
            self.movie_form_layout.addWidget(button)
        
        self.movie_group_box.setLayout(self.movie_form_layout)

        self.movie_scroll_area = QtWidgets.QScrollArea(self)
        self.movie_scroll_area.setWidgetResizable(True)
        self.movie_scroll_area.setGeometry(0, 60, 635, 600)
        self.movie_scroll_area.setWidget(self.movie_group_box)

    def create_media_button(self, media):
        button = MediaButton(media)
        button.setGeometry(0, 0, 635, 50)
        self.movie_buttons.append(button)
        return button
