from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QMenu, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PIL.ImageQt import ImageQt

from utils.media import Media, Show, Movie
from const import MEDIA_PLAYER

class MediaButton(QPushButton):
    def __init__(
            self,
            media: Media,
            media_player: str = MEDIA_PLAYER,
            speed: float = 1,
            parent=None
        ):
        super().__init__(parent)
        self.media = media
        self.media_player = media_player
        self.setCheckable(True)
        self.setFixedSize(150, 300)

        # Image display
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 220)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #222; border-radius: 4px;")
        self.image_loaded = False

        # Text label
        self.text_label = QLabel(f"{media.name} ({media.year})\n{media.rating}⭐")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.text_label.setStyleSheet("color: white;")
        self.text_label.setFixedHeight(50)

        # Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label)

        self.setLayout(layout)
        self.setStyleSheet("background-color: none; border: none;")

        self.clicked.connect(lambda: self.media.play(media_player=self.media_player, speed=speed))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        context_menu = QMenu(self)
        details = context_menu.addAction("Details")
        details.triggered.connect(self._open_details)
        open_in_explorer = context_menu.addAction("Open in files")
        open_in_explorer.triggered.connect(self.media.open_in_explorer)
        if isinstance(self.media, Show):
            rm_wached = context_menu.addAction("Delete wached")
            rm_wached.triggered.connect(self._remove_wached_folder)
        elif isinstance(self.media, Movie):
            rm_movie = context_menu.addAction("Delete movie")
            rm_movie.triggered.connect(self._remove_movie)
        if context_menu.actions():
            context_menu.exec(self.mapToGlobal(pos))

    def _open_details(self):
        print_str = f"name: {self.media.name}\n"
        print_str += f"year: {self.media.year}\n"
        print_str += f"imdb rating: {self.media.rating}\n"

        if isinstance(self.media, Movie):
            print_str += f"metacritic rating: {self.media.metacritic}\n"
            print_str += f"runtime: {self.media.runtime//60}h{self.media.runtime%60}m\n"
        elif isinstance(self.media, Show):
            print_str += f"episodes: {self.media.episodes}\n"
            print_str += f"seasons: {self.media.seasons}\n"

        print_str += f"plot: {self.media.plot}"
        print(print_str)

    def _get_main_window(self):
        current_widget = self
        while not current_widget.__class__.__name__ == 'MainGUIWindow':
            current_widget = current_widget.parent()
        return current_widget
    
    def _get_confirmation(self) -> bool:
        confirmation = QMessageBox.question(
            self._get_main_window(), 'Confirmation',
            "Are you sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return confirmation == QMessageBox.StandardButton.Yes

    def _remove_wached_folder(self):
        if not self._get_confirmation():
            return
        # assuming self.media is a Show type
        self.media.remove_wached_folder()
    
    def _remove_movie(self):
        if not self._get_confirmation():
            return
        # assuming self.media is a Movie type
        self.media.remove_movie()
        self._get_main_window()._on_refresh_button_click()

    def load_image(self):
        if not self.image_loaded:
            image = self.media.image.convert("RGBA")
            qimage = ImageQt(image)
            pixmap = QPixmap.fromImage(qimage).scaled(
                150, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
            self.image_loaded = True
    
    def unload_image(self):
        if self.image_loaded:
            self.image_label.clear()
            self.image_loaded = False