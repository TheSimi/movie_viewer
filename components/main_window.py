import dotenv
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QStackedLayout,
    QComboBox, QGridLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QPoint, QTimer, QThread

from components.media_button import MediaButton
from components.setting_menu import SettingsMenu
from media_classes import Media, Movie, Show
from qt_utils.load_media_worker import LoadMediaWorker
from utils.cache_utilis import cache_path, clean_cache
from qt_utils.push_button import PushButton
from const import MEDIA_PLAYER

SCROLL_AREA_WIDTH = 900
COMBO_BOX_WIDTH = 310

class MainGUIWindow(QMainWindow):
    def __init__(self, movie_folders, show_folders):
        super().__init__()
        self._init_ui()

        self.settings_menu = SettingsMenu(self, movie_folders, show_folders)

        self.media_buttons = []
        self.show_list: list[Show] = []
        self.movie_list: list[Movie] = []
        self.loading_threads: dict[type, QThread] = {}
        self.loading_workers: dict[type, LoadMediaWorker] = {}
        self.init_show_movie_lists(movie_folders, show_folders)
        self.media_player = MEDIA_PLAYER

    def _init_ui(self):
        self.setWindowTitle("movie_viewer")
        self.setGeometry(0, 0, 1000, 780)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack = QStackedLayout(self.central_widget)
        
        self.main_screen = QWidget()
        main_layout = QVBoxLayout(self.main_screen)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Settings button row
        settings_bar = QHBoxLayout()
        settings_bar.addStretch()
        settings_btn = PushButton("⚙️")
        settings_btn.setObjectName("SettingsButton")  # used in clear/restore
        settings_btn.setFixedSize(50, 50)
        settings_btn.setFont(QFont("Ariel", 14))
        settings_btn.clicked.connect(self.open_settings_menu)
        settings_bar.addWidget(settings_btn)
        main_layout.addLayout(settings_bar)

        # Combo box
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        top_controls_layout.setSpacing(20)

        self.list_type_combo = QComboBox()
        self.list_type_combo.addItems(["Shows", "Movies"])
        self.list_type_combo.setFixedWidth(COMBO_BOX_WIDTH)
        self.list_type_combo.setFont(QFont("Arial", 14))
        self.list_type_combo.setStyleSheet("padding: 6px;")
        self.list_type_combo.currentIndexChanged.connect(lambda: {self.update_display(), self.resort_media_list()})

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Year", "Rating", "Path", "Length"])
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.setFont(QFont("Arial", 14))
        self.sort_combo.setStyleSheet("padding: 6px;")
        self.sort_combo.currentIndexChanged.connect(self.resort_media_list)

        self.sort_label = QLabel()
        self.sort_label.setText("Sort by:")
        self.sort_label.setFont(QFont("Arial", 14))

        self.reverse_button = PushButton(style_sheet="padding: 6px;")
        self.reverse_button.setText("▼")
        self.reverse_button.setFont(QFont("Arial", 14))
        self.reverse_button.setFixedWidth(50)
        self.reverse_button.clicked.connect(self._on_reverse_button_click)
        
        self.refresh_button = PushButton(style_sheet="padding: 6px;")
        self.refresh_button.setText("⭮")
        self.refresh_button.setFont(QFont("Arial", 14))
        self.refresh_button.setFixedWidth(50)
        self.refresh_button.clicked.connect(self._on_refresh_button_click)

        top_controls_layout.addWidget(self.refresh_button)
        top_controls_layout.addWidget(self.list_type_combo)
        top_controls_layout.addWidget(self.sort_label)
        top_controls_layout.addWidget(self.sort_combo)
        top_controls_layout.addWidget(self.reverse_button)
        main_layout.addLayout(top_controls_layout)

        # Scroll area
        scroll_wrapper = QHBoxLayout()
        scroll_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(SCROLL_AREA_WIDTH)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.lazy_load_visible_buttons)

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
        self._get_media_list_async(movie_folders, Movie)
        self._get_media_list_async(show_folders, Show)
    
    def _get_media_list_async(
        self,
        folder_list: list,
        file_class: Media.__class__,
    ):
        self.loading_threads[file_class] = QThread()
        self.loading_workers[file_class] = LoadMediaWorker(folder_list, file_class)
        self.loading_workers[file_class].moveToThread(self.loading_threads[file_class])

        self.loading_threads[file_class].started.connect(self.loading_workers[file_class].run)
        self.loading_workers[file_class].finished.connect(lambda media_list: self._on_media_loaded(media_list, file_class))
        self.loading_threads[file_class].finished.connect(self.loading_threads[file_class].deleteLater)
    
        self.loading_threads[file_class].start()
    
    def _on_media_loaded(self, media_list, file_class):
        if file_class == Movie:
            self.movie_list = media_list
        else:
            self.show_list = media_list
        
        self.resort_media_list()
    
    def load_file_list(
        self,
        file_path_list: list,
        file_class: Media.__class__,
    ) -> list: 
        file_list = []
        for file in file_path_list:
            if os.path.exists(cache_path(file)):
                file_list.append(file_class.from_cache(cache_path(file)))
            else:
                instance = file_class(file)
                file_list.append(instance)
                instance.save_to_cache()
        return file_list

    def open_settings_menu(self):
        self.settings_menu.exec()

        new_movie_folders = self.settings_menu.movie_folders
        new_show_folders = self.settings_menu.show_folders
        self.media_player = self.settings_menu.media_player_edit.text()

        self.init_show_movie_lists(new_movie_folders, new_show_folders)
        self.resort_media_list()

    def update_display(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_list = self.show_list if self.list_type_combo.currentText() == "Shows" else self.movie_list
        current_speed = self.settings_menu.speed_spin.value()

        self.media_buttons = []
        for idx, media in enumerate(current_list):
            button = MediaButton(media, self.media_player, current_speed)
            self.media_buttons.append(button)
            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(button, row, col)
        
        QTimer.singleShot(50, self.lazy_load_visible_buttons)
    
    def resort_media_list(self):
        sort_option = self.sort_combo.currentText()
        current_type = self.list_type_combo.currentText()
        reverse_sorting = True if self.reverse_button.text() == "▲" else False

        # Get the correct list to sort
        media_list = self.show_list if current_type == "Shows" else self.movie_list

        # Sorting logic
        if sort_option == "Name":
            media_list.sort(key=self._sort_by_name, reverse=reverse_sorting)
        elif sort_option == "Year":
            media_list.sort(key=self._sort_by_year, reverse=reverse_sorting)
        elif sort_option == "Rating":
            media_list.sort(key=self._sort_by_rating, reverse=reverse_sorting)
        elif sort_option == "Path":
            media_list.sort(key=self._sort_by_path, reverse=reverse_sorting)
        elif sort_option == "Length":
            media_list.sort(key=self._sort_by_length, reverse=reverse_sorting)
        
        self.update_display()
    
    @staticmethod
    def _sort_by_name(media: Media):
        year, rating, name, _, _ = media._get_values()
        return name.lower(), -rating, -year
    
    @staticmethod
    def _sort_by_year(media: Media):
        year, rating, name, _, _ = media._get_values()
        return -year, -rating, name.lower()
    
    @staticmethod
    def _sort_by_rating(media: Media):
        year, rating, name, _, _ = media._get_values()
        return -rating, -year, name.lower()
    
    @staticmethod
    def _sort_by_path(media: Media):
        _, _, _, path, _ = media._get_values()
        return path
    
    @staticmethod
    def _sort_by_length(media: Media):
        year, rating, name, _, length = media._get_values()
        return length, -rating, -year, name.lower()

    def _on_reverse_button_click(self):
        if self.reverse_button.text() == "▼":
            self.reverse_button.setText("▲")
        elif self.reverse_button.text() == "▲":
            self.reverse_button.setText("▼")
        self.resort_media_list()
    
    def _on_refresh_button_click(self):
        new_movie_folders = self.settings_menu.movie_folders
        new_show_folders = self.settings_menu.show_folders

        self.init_show_movie_lists(new_movie_folders, new_show_folders)
        self.resort_media_list()

    def lazy_load_visible_buttons(self):
        scroll_value = self.scroll_area.verticalScrollBar().value()

        # Get scroll area's visible rectangle
        visible_rect = self.scroll_area.viewport().rect()
        visible_top = scroll_value
        visible_bottom = scroll_value + visible_rect.height()

        # Load images for buttons whose vertical position is within view
        for btn in self.media_buttons:
            # Get button's Y position relative to scroll area content
            btn_y = btn.mapTo(self.scroll_area.widget(), QPoint(0, 0)).y()
            if visible_top - 200 < btn_y < visible_bottom + 200:  # preload a bit outside view
                btn.load_image()
            else:
                btn.unload_image()
    
    def closeEvent(self, event, *args, **kwargs):
        # Save the new folder paths from the settings to the .env file
        new_movie_folders = self.settings_menu.movie_folders
        new_show_folders = self.settings_menu.show_folders
        current_speed = str(round(self.settings_menu.speed_spin.value(), 1))

        current_media_player = self.settings_menu.media_player_edit.text()
        
        new_movie_folder_const = ",".join(new_movie_folders)
        new_show_folder_const = ",".join(new_show_folders)
        dotenv.set_key(dotenv.find_dotenv(), "MOVIE_FOLDERS", new_movie_folder_const)
        dotenv.set_key(dotenv.find_dotenv(), "SHOW_FOLDERS", new_show_folder_const)
        dotenv.set_key(dotenv.find_dotenv(), "MEDIA_PLAYER", current_media_player)
        dotenv.set_key(dotenv.find_dotenv(), "SPEED",  current_speed)

        clean_cache(self.movie_list, self.show_list, )

        super().closeEvent(event)
    
    def showMaximized(self):
        super().showMaximized()
        self.update_display()
