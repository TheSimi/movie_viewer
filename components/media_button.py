from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QMenu, QMessageBox, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PIL.ImageQt import ImageQt

from utils.media import Media, Show, Movie
from components.details_window import MediaDetailsDialog
from const import MEDIA_PLAYER

IDLE_BUTTON_STYLESHEET = "border: 2px solid #222; background-color: none; border-radius: 4px;"
FOCUSED_BUTTON_STYLESHEET = "border: 2px solid white; background-color: none; border-radius: 4px;"
TEXT_LABEL_STYLESHEET = "color: white; background: none; border: none;"
IMAGE_LABEL_STYLESHEET = "background: none; border: none;"

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
        self.setStyleSheet(IDLE_BUTTON_STYLESHEET)

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
            self.length_label = QLabel(f"[ {media.runtime//60:02d}:{media.runtime%60:02d} ]")
            self.length_label.setWordWrap(True)
            self.length_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.length_label.setStyleSheet(TEXT_LABEL_STYLESHEET)
            self.main_layout.addWidget(self.length_label)

        self.setLayout(self.main_layout)

        self.clicked.connect(lambda: self.media.play(media_player=self.media_player, speed=speed))

        self.enterEvent = lambda arg: self.setStyleSheet(FOCUSED_BUTTON_STYLESHEET)
        self.leaveEvent = lambda arg: self.setStyleSheet(IDLE_BUTTON_STYLESHEET)
        self.focusInEvent = lambda arg: self.setStyleSheet(FOCUSED_BUTTON_STYLESHEET)
        self.focusOutEvent = lambda arg: self.setStyleSheet(IDLE_BUTTON_STYLESHEET)

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
        details_win = MediaDetailsDialog(self.media, self.main_window)
        details_win.show()

    @property
    def main_window(self) -> QMainWindow:
        current_widget = self
        while not current_widget.__class__.__name__ == 'MainGUIWindow':
            current_widget = current_widget.parent()
        return current_widget
    
    def _get_confirmation(self) -> bool:
        confirmation = QMessageBox.question(
            self.main_window, 'Confirmation',
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
        self.main_window._on_refresh_button_click()

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