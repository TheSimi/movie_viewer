import dotenv
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel,
    QComboBox, QSizePolicy, QGridLayout, QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PIL.ImageQt import ImageQt

from setting_menu import SettingsMenu
from const import MOVIE_FOLDERS, SHOW_FOLDERS
from get_lists import get_file_list, get_movies_in_folder, get_shows_in_folder
from media import Movie, Show
from cache_utilis import clear_cache

class MediaButton(QPushButton):
    def __init__(self, media):
        super().__init__()
        self.media = media

        self.setFixedSize(150, 250)
        self.setStyleSheet("border: none;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Convert PIL image to QPixmap
        qt_image = ImageQt(self.media.image.copy())
        pixmap = QPixmap.fromImage(qt_image).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(media.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 13px;")

        layout.addWidget(image_label)
        layout.addWidget(name_label)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.clicked.connect(self.media.play)

class MainGUIWindow(QMainWindow):
    def __init__(self, show_list, movie_list):
        super().__init__()
        self.setWindowTitle("Media Browser")
        self.setGeometry(0, 0, 1000, 780)

        self.show_list = show_list
        self.movie_list = movie_list

        # ─── Central Widget ───
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(20)

        # ─── Settings Button Top-Right ───
        settings_bar = QHBoxLayout()
        settings_bar.addStretch()
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedSize(100, 32)
        settings_btn.clicked.connect(self.open_settings_menu)
        settings_bar.addWidget(settings_btn)
        outer_layout.addLayout(settings_bar)

        # ─── Centered ComboBox ───
        combo_wrapper = QHBoxLayout()
        combo_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["Shows", "Movies"])
        self.combo_box.setFixedWidth(680)
        self.combo_box.setFont(QFont("Arial", 14))
        self.combo_box.setStyleSheet("padding: 6px;")
        self.combo_box.currentIndexChanged.connect(self.update_display)

        combo_wrapper.addWidget(self.combo_box)
        outer_layout.addLayout(combo_wrapper)

        # ─── Centered Scroll Area ───
        scroll_wrapper = QHBoxLayout()
        scroll_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(680)  # wider now
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_wrapper.addWidget(self.scroll_area)
        outer_layout.addLayout(scroll_wrapper)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)

        self.update_display()

        self.settings_window = SettingsMenu(self, MOVIE_FOLDERS, SHOW_FOLDERS)

    def open_settings_menu(self):
        self.settings_window.exec()
        new_movie_folders = self.settings_window.movie_folders
        new_show_folders = self.settings_window.show_folders

        self.movie_list = get_file_list(new_movie_folders, get_movies_in_folder, Movie)
        self.show_list = get_file_list(new_show_folders, get_shows_in_folder, Show)
        self.update_display()

    def update_display(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_list = self.show_list if self.combo_box.currentText() == "Shows" else self.movie_list

        for idx, media in enumerate(current_list):
            button = MediaButton(media)
            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(button, row, col)
    
    def closeEvent(self, event):
        print("Closing main window...")

        # Save the new folder paths from the settings to the .env file
        new_movie_folders = self.settings_window.movie_folders
        new_show_folders = self.settings_window.show_folders
        
        new_movie_folder_const = ",".join(new_movie_folders)
        new_show_folder_const = ",".join(new_show_folders)
        dotenv.set_key(dotenv.find_dotenv(), "MOVIE_FOLDERS", new_movie_folder_const)
        dotenv.set_key(dotenv.find_dotenv(), "SHOW_FOLDERS", new_show_folder_const)

        clear_cache(self.movie_list, self.show_list)

        super().closeEvent(event)