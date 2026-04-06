from functools import cached_property

from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QMainWindow, QMenu, QMessageBox, QVBoxLayout

from components.details_window import MediaDetailsDialog
from components.play_window import PlayWindow
from components.search_window import SearchWindow
from const import IMAGE_LABEL_STYLESHEET, MEDIA_PLAYER, TEXT_LABEL_STYLESHEET
from media_classes import Media, Movie, Show
from qt_utils.push_button import PushButton


class MediaButton(PushButton):
    def __init__(
        self,
        media: Media,
        media_player: str = MEDIA_PLAYER,
        speed: float = 1,
        parent=None,
    ):
        super().__init__(parent)
        self.media = media
        self.speed = speed
        self.media_player = media_player
        self.setCheckable(True)
        self.setFixedSize(200, 330)

        # Image display
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 220)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(IMAGE_LABEL_STYLESHEET)
        self.image_loaded = False

        # Text label
        self.name_year_label = QLabel(f"{media.name} ({media.year})")
        self.name_year_label.setWordWrap(True)
        self.name_year_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.name_year_label.setStyleSheet(TEXT_LABEL_STYLESHEET)

        self.rating_label = QLabel(f"{media.rating}⭐")
        self.rating_label.setWordWrap(True)
        self.rating_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.rating_label.setStyleSheet(TEXT_LABEL_STYLESHEET)

        # Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.image_label)
        self.main_layout.addWidget(self.name_year_label)
        self.main_layout.addWidget(self.rating_label)

        if isinstance(self.media, Movie):
            self.length_label = QLabel(
                f"[ {self.media.runtime // 60:02d}:{self.media.runtime % 60:02d} ]"
            )
            self.length_label.setWordWrap(True)
            self.length_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.length_label.setStyleSheet(TEXT_LABEL_STYLESHEET)
            self.main_layout.addWidget(self.length_label)

        self.setLayout(self.main_layout)

        self.clicked.connect(
            lambda: self.media.play(media_player=self.media_player, speed=self.speed)
        )

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        context_menu = QMenu(self)

        play = context_menu.addAction("Play")
        play.triggered.connect(self._open_play_window)

        details = context_menu.addAction("Details")
        details.triggered.connect(self._open_details)

        open_in_explorer = context_menu.addAction("Open in files")
        open_in_explorer.triggered.connect(self.media.open_in_explorer)

        reload = context_menu.addAction("Reload")
        reload.triggered.connect(self._del_cache_and_reload)

        search = context_menu.addAction("Search Matches")
        search.triggered.connect(self._open_search)

        if isinstance(self.media, Show):
            rm_wached = context_menu.addAction("Delete watched")
            rm_wached.triggered.connect(self._remove_watched_folder)
        elif isinstance(self.media, Movie):
            rm_movie = context_menu.addAction("Delete movie")
            rm_movie.triggered.connect(self._remove_movie)
        if context_menu.actions():
            context_menu.exec(self.mapToGlobal(pos))

    def _open_search(self):
        search_win = SearchWindow(self.media, self.main_window)
        search_win.show()

    def _open_details(self):
        details_win = MediaDetailsDialog(self.media, self.main_window)
        details_win.show()

    def _open_play_window(self):
        play_win = PlayWindow(self.media, self.speed)
        play_win.exec()

    def _del_cache_and_reload(self):
        self.media.delete_cache()
        self.main_window._on_refresh_button_click()  # type: ignore

    @cached_property
    def main_window(self) -> QMainWindow:
        """
        Returns the main window of the application.

        :return: The main window instance.
        :rtype: MainGUIWindow
        """
        current_widget = self
        while not current_widget.__class__.__name__ == "MainGUIWindow":
            current_widget = current_widget.parent()
        return current_widget  # type: ignore

    def _get_confirmation(self) -> bool:
        confirmation = QMessageBox.question(
            self.main_window,
            "Confirmation",
            "Are you sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return confirmation == QMessageBox.StandardButton.Yes

    def _remove_watched_folder(self):
        if not isinstance(self.media, Show) or not self._get_confirmation():
            return
        self.media.remove_watched_folder()

    def _remove_movie(self):
        if not isinstance(self.media, Movie) or not self._get_confirmation():
            return
        self.media.remove_movie()
        self.main_window._on_refresh_button_click()  # type: ignore

    def load_image(self):
        if not self.image_loaded:
            image = self.media.image.convert("RGBA")
            qimage = ImageQt(image)
            pixmap = QPixmap.fromImage(qimage).scaled(
                150,
                220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(pixmap)
            self.image_loaded = True

    def unload_image(self):
        if self.image_loaded:
            self.image_label.clear()
            self.image_loaded = False
