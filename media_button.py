from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PIL.ImageQt import ImageQt

from media import Media
from const import MEDIA_PLAYER

class MediaButton(QPushButton):
    def __init__(self, media: Media, media_player: str = MEDIA_PLAYER, parent=None):
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

        self.clicked.connect(lambda: self.media.play(media_player=self.media_player))

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