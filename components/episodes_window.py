from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from const import MEDIA_PLAYER
from media_classes.show import Show


class EpisodesWindow(QDialog):
    def __init__(
        self,
        show: Show,
        media_player: str = MEDIA_PLAYER,
        speed: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self.media = show
        self.media_player = media_player
        self.speed = speed

        self.setWindowTitle(f"Episodes - {show.name}")
        self.setBaseSize(500, 400)

        main_layout = QVBoxLayout()

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        scroll_content_widget = QWidget()
        self.scroll_content_layout = QVBoxLayout(scroll_content_widget)

        self.populate_episodes()

        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)

    def populate_episodes(self):
        unwatched = self.media.episode_list
        watched = self.media.watched_episode_list

        for episode_name in unwatched:
            episode_widget = EpisodeRow(episode_name, is_watched=False, parent=self)
            self.scroll_content_layout.addWidget(episode_widget)

        for episode_name in watched:
            episode_widget = EpisodeRow(episode_name, is_watched=True, parent=self)
            self.scroll_content_layout.addWidget(episode_widget)

        self.scroll_content_layout.addStretch()

    def refresh_episodes(self):
        while self.scroll_content_layout.count():
            child = self.scroll_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.populate_episodes()

    def play_episode(self, episode_name: str):
        self.media.play_episode(
            episode_name,
            media_player=self.media_player,
            speed=self.speed,
            move_to_watched=False,
        )

    def toggle_watched(self, episode_name: str):
        self.media.toggle_watched(episode_name)
        self.refresh_episodes()


class EpisodeRow(QWidget):
    def __init__(
        self,
        episode_name: str,
        is_watched: bool,
        parent: EpisodesWindow,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        name_label = QLabel(
            f"<b>{'watched' if is_watched else 'unwatched'}</b>: {episode_name}"
        )

        play_button = QPushButton("Play")
        play_button.clicked.connect(
            lambda: parent.play_episode(episode_name)
        )

        watched_checkbox = QCheckBox("Watched")
        watched_checkbox.setChecked(is_watched)
        watched_checkbox.clicked.connect(
            lambda: parent.toggle_watched(episode_name)
        )

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(play_button)
        layout.addWidget(watched_checkbox)
