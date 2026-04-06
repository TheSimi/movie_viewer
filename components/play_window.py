from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QVBoxLayout

from const import MEDIA_PLAYER
from media_classes import Media
from qt_utils.push_button import PushButton


class PlayWindow(QDialog):
    def __init__(
        self,
        media: Media,
        default_speed: float = 1,
        media_player: str = MEDIA_PLAYER,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle(f"Play {media.name}")
        self.setFixedSize(300, 150)

        self.media = media
        self.media_player = media_player

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Video Speed SpinBox
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Speed:")
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 2.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.setValue(default_speed if 0.1 < default_speed < 2.0 else 1.0)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_spinbox)
        main_layout.addLayout(speed_layout)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        self.cancel_button = PushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.play_button = PushButton("Play")
        self.play_button.setDefault(True)
        self.play_button.clicked.connect(self.play_media_and_close)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.play_button)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.setModal(True)

    def play_media_and_close(self):
        self.media.play(self.media_player, self.speed_spinbox.value())
        self.accept()
