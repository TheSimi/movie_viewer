import dotenv
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QStackedLayout,
    QComboBox, QSizePolicy, QGridLayout, QPushButton, QHBoxLayout, QProgressBar
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PIL.ImageQt import ImageQt

from get_lists import get_file_list, get_movies_in_folder, get_shows_in_folder
from setting_menu import SettingsMenu
from const import MOVIE_FOLDERS, SHOW_FOLDERS
from media import Movie, Show, Media
from cache_utilis import clear_cache, cache_path

SCROLL_AREA_WIDTH = 680

class MediaButton(QPushButton):
    def __init__(self, media):
        super().__init__()
        self.media = media

        self.setFixedSize(150, 280)
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

        name_string = f"{self.media.name} ({self.media.year})"
        name_label = QLabel(name_string)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 13px;")

        rating_string = f"⭐ {self.media.rating}"
        rating_label = QLabel(rating_string)
        rating_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rating_label.setWordWrap(True)
        rating_label.setStyleSheet("font-size: 13px;")

        layout.addWidget(image_label)
        layout.addWidget(name_label)
        layout.addWidget(rating_label)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.clicked.connect(self.media.play)

class MainGUIWindow(QMainWindow):
    def __init__(self, movie_folders, show_folders):
        super().__init__()
        self.setWindowTitle("movie_viewer")
        self.setGeometry(0, 0, 1000, 780)

        # ─── CENTRAL WIDGET ───
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack = QStackedLayout(self.central_widget)

        self._init_main_screen()

        self.settings_window = SettingsMenu(self, movie_folders, show_folders)

        self.init_show_movie_lists(movie_folders, show_folders)

    def _init_main_screen(self):
        self.main_screen = QWidget()
        main_layout = QVBoxLayout(self.main_screen)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()  # hidden by default
        main_layout.addWidget(self.progress_bar)

        # Settings button row
        settings_bar = QHBoxLayout()
        settings_bar.addStretch()
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SettingsButton")  # used in clear/restore
        settings_btn.setFixedSize(100, 32)
        settings_btn.clicked.connect(self.open_settings_menu)
        settings_bar.addWidget(settings_btn)
        main_layout.addLayout(settings_bar)

        # Combo box
        combo_wrapper = QHBoxLayout()
        combo_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["Shows", "Movies"])
        self.combo_box.setFixedWidth(SCROLL_AREA_WIDTH)
        self.combo_box.setFont(QFont("Arial", 14))
        self.combo_box.setStyleSheet("padding: 6px;")
        self.combo_box.currentIndexChanged.connect(self.update_display)

        combo_wrapper.addWidget(self.combo_box)
        main_layout.addLayout(combo_wrapper)

        # Scroll area
        scroll_wrapper = QHBoxLayout()
        scroll_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(SCROLL_AREA_WIDTH)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_wrapper.addWidget(self.scroll_area)
        main_layout.addLayout(scroll_wrapper)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)

        self.stack.addWidget(self.main_screen)
        self.stack.setCurrentWidget(self.main_screen)

    def init_show_movie_lists(self, movie_folders, show_folders):
        self.movie_list = self._get_media_list(movie_folders, get_movies_in_folder, Movie)
        self.show_list = self._get_media_list(show_folders, get_shows_in_folder, Show)
    
    def _get_media_list(
        self,
        folder_list: list,
        file_in_folder_func: callable,
        file_class: Media,
    ) -> list:
        file_path_list = get_file_list(folder_list, file_in_folder_func)

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(file_path_list))

        media_list = self.load_file_list(file_path_list, file_class)

        self.progress_bar.hide()
        return media_list
    
    def load_file_list(
        self,
        file_path_list: list,
        file_class: Media,
    ) -> list:
        file_list = []
        for file in file_path_list:
            if os.path.exists(cache_path(file)):
                file_list.append(file_class.load_from_cache(cache_path(file)))
            else:
                instance = file_class(file)
                file_list.append(instance)
                instance.save_to_cache()
            
            self.progress_bar.setValue(self.progress_bar.value() + 1)

        return file_list

    def open_settings_menu(self):
        self.settings_window.exec()
        new_movie_folders = self.settings_window.movie_folders
        new_show_folders = self.settings_window.show_folders

        self.init_show_movie_lists(new_movie_folders, new_show_folders)
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
    
    def show(self):
        super().show()

        self.update_display()
