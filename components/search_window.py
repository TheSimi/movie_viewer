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
from services.movie_client import MovieClient
from services.show_client import ShowClient


class SearchWindow(QDialog):
    def __init__(self, media: Media, parent=None):
        super().__init__(parent)
        self.media = media
        self.client = MovieClient if isinstance(media, Movie) else ShowClient

        self.setWindowTitle(f"Search {self.media.name}")
        self.setBaseSize(400, 300)

        main_layout = QVBoxLayout()

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(scroll_content_widget)
        self.populate_search_results()

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def populate_search_results(self):
        search_results = self.client.get_search_results(self.media.name)
        for result in search_results:
            search_result_widget = SearchResult(**result, parent=self)
            self.scroll_content_layout.addWidget(search_result_widget)

    def choose_result(self, imdb_id):
        self.media.delete_cache()
        media_class = Movie if isinstance(self.media, Movie) else Show
        new_media = media_class(self.media.path, id=imdb_id)
        self.parent().replace_media(self.media, new_media)  # type: ignore
        self.accept()


class SearchResult(QWidget):
    def __init__(self, name, year, id, imdb_url, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        name_label = QLabel(f"<b>name</b>: {name} ({year})")

        separator = QLabel("|")

        imdb_label = QLabel(
            f"<b>imdb</b>: <a href='{imdb_url}' style='color: #4a9eff;'>{id}</a>"
        )
        imdb_label.setOpenExternalLinks(True)

        choose_button = QPushButton("Choose")
        choose_button.clicked.connect(lambda: parent.choose_result(id))

        layout.addWidget(name_label)
        layout.addWidget(separator)
        layout.addWidget(imdb_label)
        layout.addWidget(choose_button)

        layout.addStretch()
