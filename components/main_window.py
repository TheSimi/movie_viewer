import json

from PyQt6.QtCore import QPoint, QSize, Qt, QThread, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)
from pyqtwaitingspinner import SpinnerParameters, WaitingSpinner
from pyqtwaitingspinner.parameters import QColor

from components.media_button import MediaButton
from components.setting_menu import SettingsMenu
from const import (
    CONFIG_PATH,
    DOWN_ARROW_PATH,
    MEDIA_PLAYER,
    REFRESH_ICON_PATH,
    SETTINGS_ICON_PATH,
    UP_ARROW_PATH,
)
from media_classes import Media, Movie, Show
from qt_utils.load_media_worker import LoadMediaWorker
from services.logger import logger
from utils.cache_utilis import clean_cache

UP_ARROW_ICON = QIcon(UP_ARROW_PATH)
DOWN_ARROW_ICON = QIcon(DOWN_ARROW_PATH)


class MainGUIWindow(QMainWindow):
    def __init__(self, movie_folders, show_folders):
        super().__init__()
        self._init_ui()

        self.settings_menu = SettingsMenu(self, movie_folders, show_folders)

        self._init_media(movie_folders, show_folders)
        self.media_player = MEDIA_PLAYER

    def _init_ui(self):
        self.setWindowTitle("movie_viewer")
        self.setGeometry(0, 0, 1000, 780)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack = QStackedLayout(self.central_widget)

        self.main_screen = QWidget()
        self.main_screen.setObjectName("MainScreen")
        main_layout = QVBoxLayout(self.main_screen)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Settings button row
        settings_bar = QHBoxLayout()
        settings_bar.addStretch()
        settings_btn = QPushButton()
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setIcon(QIcon(SETTINGS_ICON_PATH))
        settings_btn.setIconSize(QSize(28, 28))
        settings_btn.setFixedSize(50, 50)
        settings_btn.clicked.connect(self.open_settings_menu)
        settings_bar.addWidget(settings_btn)
        main_layout.addLayout(settings_bar)

        # Combo box
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        top_controls_layout.setSpacing(20)

        self.list_type_combo = QComboBox()
        self.list_type_combo.setObjectName("ListTypeCombo")
        self.list_type_combo.addItems(["Shows", "Movies"])
        self.list_type_combo.setFixedSize(310, 40)
        self.list_type_combo.currentIndexChanged.connect(
            lambda: {self.update_display(), self.resort_media_list()}
        )

        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("SortCombo")
        self.sort_combo.addItems(["Name", "Year", "Rating", "Path", "Length"])
        self.sort_combo.setFixedSize(120, 40)
        self.sort_combo.currentIndexChanged.connect(self.resort_media_list)

        self.sort_label = QLabel()
        self.sort_label.setObjectName("SortLabel")
        self.sort_label.setText("Sort by:")

        self._is_media_list_reversed = False

        self.reverse_button = QPushButton()
        self.reverse_button.setObjectName("ReverseButton")
        self.reverse_button.setIcon(DOWN_ARROW_ICON)
        self.reverse_button.setIconSize(QSize(20, 20))
        self.reverse_button.setFixedSize(50, 40)
        self.reverse_button.clicked.connect(self._on_reverse_button_click)

        self.refresh_button = QPushButton()
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setIcon(QIcon(REFRESH_ICON_PATH))
        self.refresh_button.setIconSize(QSize(20, 20))
        self.refresh_button.setFixedSize(50, 40)
        self.refresh_button.clicked.connect(self._on_refresh_button_click)

        loading_spinner_parameters = SpinnerParameters(
            roundness=100.0,
            trail_fade_percentage=75.0,
            number_of_lines=100,
            line_length=6,
            line_width=6,
            inner_radius=8,
            revolutions_per_second=1.5,
            color=QColor(200, 200, 200),
            minimum_trail_opacity=0.0,
            center_on_parent=False,
            disable_parent_when_spinning=False,
        )
        self.loading_spinner = WaitingSpinner(
            self, spinner_parameters=loading_spinner_parameters
        )
        self.loading_spinner.start()
        self.loading_spinner.hide()

        top_controls_layout.addWidget(self.loading_spinner)
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
        self.scroll_area.setFixedWidth(900)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.verticalScrollBar().valueChanged.connect(
            self.lazy_load_visible_buttons
        )

        scroll_wrapper.addWidget(self.scroll_area)
        main_layout.addLayout(scroll_wrapper)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)

        self.stack.addWidget(self.main_screen)
        self.stack.setCurrentWidget(self.main_screen)

    def _init_media(self, movie_folders, show_folders):
        self.media_buttons = []
        self.media_lists: dict[type, list[Media]] = {Movie: [], Show: []}
        self.loading_threads: dict[type, QThread] = {}
        self.loading_workers: dict[type, LoadMediaWorker] = {}

        self.load_show_movie_lists(movie_folders, show_folders)

    def load_show_movie_lists(self, movie_folders, show_folders):
        """
        Load the movie and show lists, each in a separate thread
        """
        self._get_media_list_async(movie_folders, Movie)
        self._get_media_list_async(show_folders, Show)

    def _get_media_list_async(
        self,
        folder_list: list,
        file_class: Media.__class__,
    ):
        # Check if we are in the process of loading
        self.loading_spinner.show()

        if self.loading_threads.get(file_class, None) or self.loading_workers.get(
            file_class, None
        ):
            logger.warning(
                f"Already loading {file_class.__name__} list, skipping new load request."
            )
            return

        # Init worker and thread
        self.loading_threads[file_class] = QThread()
        self.loading_workers[file_class] = LoadMediaWorker(folder_list, file_class)
        self.loading_workers[file_class].moveToThread(self.loading_threads[file_class])

        # Connect signals for start and end
        self.loading_threads[file_class].started.connect(
            self.loading_workers[file_class].run
        )
        self.loading_workers[file_class].finished.connect(
            lambda media_list: self._on_media_loaded(media_list, file_class)
        )

        # Clean up thread and worker after finishing
        self.loading_threads[file_class].finished.connect(
            self.loading_threads[file_class].deleteLater
        )
        self.loading_threads[file_class].finished.connect(
            lambda: self.loading_threads.pop(file_class, None)
        )

        # Start loading in the background
        self.loading_threads[file_class].start()

    def _on_media_loaded(self, media_list, file_class):
        # Update media list
        self.media_lists[file_class] = media_list

        # Clean up workers
        self.loading_workers[file_class].deleteLater()
        self.loading_workers.pop(file_class, None)

        # Close thread
        self.loading_threads[file_class].quit()
        self.loading_threads[file_class].wait()

        # Update display
        self.resort_media_list()
        if not self.loading_workers:
            self.loading_spinner.hide()

    def open_settings_menu(self):
        """
        Open the settings menu, and update the settings when done
        """
        self.settings_menu.exec()

        self.media_player = self.settings_menu.media_player_edit.text()

        self.load_show_movie_lists(
            self.settings_menu.movie_folders, self.settings_menu.show_folders
        )

    def update_display(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_list = self.media_lists[
            Show if self.list_type_combo.currentText() == "Shows" else Movie
        ]
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

        # Get the correct list to sort
        media_list = self.media_lists[Show if current_type == "Shows" else Movie]

        # Sorting logic
        match sort_option:
            case "Name":
                media_list.sort(
                    key=self._sort_by_name, reverse=self._is_media_list_reversed
                )
            case "Year":
                media_list.sort(
                    key=self._sort_by_year, reverse=self._is_media_list_reversed
                )
            case "Rating":
                media_list.sort(
                    key=self._sort_by_rating, reverse=self._is_media_list_reversed
                )
            case "Path":
                media_list.sort(
                    key=self._sort_by_path, reverse=self._is_media_list_reversed
                )
            case "Length":
                media_list.sort(
                    key=self._sort_by_length, reverse=self._is_media_list_reversed
                )

        self.update_display()

    def replace_media(self, old_media: Media, new_media: Media):
        media_list = self.media_lists[old_media.__class__]
        try:
            idx = media_list.index(old_media)
            media_list[idx] = new_media
            self.resort_media_list()
        except ValueError:
            logger.warning(
                f"Old media {old_media.name} not found in list, appending new media."
            )
            media_list.append(new_media)

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
        current_icon = UP_ARROW_ICON if self._is_media_list_reversed else DOWN_ARROW_ICON
        self._is_media_list_reversed = not self._is_media_list_reversed
        self.reverse_button.setIcon(current_icon)
        self.resort_media_list()

    def _on_refresh_button_click(self):
        self.load_show_movie_lists(
            self.settings_menu.movie_folders, self.settings_menu.show_folders
        )

    def lazy_load_visible_buttons(self):
        scroll_value = self.scroll_area.verticalScrollBar().value()

        # Get scroll area's visible rectangle
        visible_rect = self.scroll_area.viewport().rect()
        visible_top = scroll_value
        visible_bottom = scroll_value + visible_rect.height()

        # Load images for buttons whose vertical position is within view
        for button in self.media_buttons:
            # Get button's Y position relative to scroll area content
            btn_y = button.mapTo(self.scroll_area.widget(), QPoint(0, 0)).y()
            if (
                visible_top - 200 < btn_y < visible_bottom + 200
            ):  # preload a bit outside view
                button.load_image()
            else:
                button.unload_image()

    def closeEvent(self, event, *args, **kwargs):  # noqa: ARG002
        new_config = {
            "movie_folders": self.settings_menu.movie_folders,
            "show_folders": self.settings_menu.show_folders,
            "media_player": self.settings_menu.media_player_edit.text(),
            "speed": round(self.settings_menu.speed_spin.value(), 1),
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(new_config, f, indent=4)

        clean_cache(self.media_lists)

        super().closeEvent(event)

    def showMaximized(self):
        super().showMaximized()
        self.update_display()
