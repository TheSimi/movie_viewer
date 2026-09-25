from typing import TYPE_CHECKING, Any, cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from media_classes.media import Media
from media_classes.movie import Movie
from media_classes.show import Show
from qt_utils.load_media_worker import run_in_background
from services.logger import logger
from services.movie_client import MovieClient
from services.show_client import ShowClient

if TYPE_CHECKING:
    from components.main_window import MainGUIWindow


class SearchWindow(QDialog):
    def __init__(self, media: Media, parent=None):
        super().__init__(parent)
        self.media = media
        self.client = MovieClient if isinstance(media, Movie) else ShowClient
        self._is_choosing = False

        self.setWindowTitle(f"Search {self.media.name}")
        self.setBaseSize(400, 300)

        main_layout = QVBoxLayout()

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(scroll_content_widget)

        self.status_label = QLabel()
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.scroll_content_layout.addWidget(self.status_label)

        self.populate_search_results()

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def populate_search_results(self):
        self.status_label.setText("Searching...")
        run_in_background(
            lambda: self.client.get_search_results(self.media.name),
            self._populate_search_results,
            self._on_search_failed,
        )

    def _populate_search_results(self, search_results: list[dict[str, Any]]) -> None:
        self.status_label.clear()
        if not search_results:
            self.status_label.setText("No results found.")
        for result in search_results:
            search_result_widget = SearchResult(**result, parent=self)
            self.scroll_content_layout.addWidget(search_result_widget)

    def _on_search_failed(self, error: str) -> None:
        self.status_label.setText(f"Search failed: {error}")

    def choose_result(self, imdb_id: str) -> None:
        if self._is_choosing:
            return
        self._is_choosing = True
        self.media.delete_cache()
        media_class = Movie if isinstance(self.media, Movie) else Show
        self.status_label.setText("Loading media...")
        run_in_background(
            lambda: media_class(self.media.path, id=imdb_id),
            self._on_media_chosen,
            self._on_choose_failed,
        )

    def _on_media_chosen(self, new_media: Media) -> None:
        parent = self.parent()
        if parent:
            main_window = cast("MainGUIWindow", parent)
            main_window.replace_media(self.media, new_media)
        self.accept()

    def _on_choose_failed(self, error: str) -> None:
        self._is_choosing = False
        logger.warning(f"[SearchWindow] Failed to load chosen media: {error}")
        self.status_label.setText(f"Failed to load media: {error}")


class SearchResult(QWidget):
    def __init__(self, name, year, id, imdb_url, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        name_label = QLabel(f"<b>name</b>: {name} ({year})")

        separator = QLabel("|")

        imdb_label = QLabel(f"<b>imdb</b>: <a href='{imdb_url}'>{id}</a>")
        imdb_label.setOpenExternalLinks(True)

        choose_button = QPushButton("Choose")
        choose_button.clicked.connect(lambda: parent.choose_result(id))

        layout.addWidget(name_label)
        layout.addWidget(separator)
        layout.addWidget(imdb_label)
        layout.addWidget(choose_button)

        layout.addStretch()
