from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QWidget, QScrollArea

from media_classes import Media, Movie, Show

class MediaDetailsDialog(QDialog):
    def __init__(self, media: Media, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(f"Details for {media.name}")
        self.setBaseSize(400, 300)

        main_layout = QVBoxLayout()
        
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        scroll_content_widget = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content_widget)
        
        path_label = QLabel(f"<b>Path:</b> {media.path}")
        path_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        scroll_content_layout.addWidget(path_label)

        name_label = QLabel(f"<b>Name:</b> {media.name}")
        name_label.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        scroll_content_layout.addWidget(name_label)
        
        rating_label = QLabel(f"<b>Rating:</b> {media.rating}")
        rating_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        scroll_content_layout.addWidget(rating_label)
        
        if isinstance(media, Movie):
            runtime_label = QLabel(f"<b>Runtime:</b> {media.runtime}")
            runtime_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            scroll_content_layout.addWidget(runtime_label)
        elif isinstance(media, Show):
            episodes_label = QLabel(f"<b>Episodes:</b> {media.episodes}")
            episodes_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            scroll_content_layout.addWidget(episodes_label)
            
            seasons_label = QLabel(f"<b>Seasons:</b> {media.seasons}")
            seasons_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            scroll_content_layout.addWidget(seasons_label)

        year_label = QLabel(f"<b>Year:</b> {media.year}")
        year_label.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        scroll_content_layout.addWidget(year_label)

        plot_label = QLabel(f"<b>Plot:</b> {media.plot}")
        plot_label.setWordWrap(True)
        plot_label.setStyleSheet("font-size: 12px;")
        scroll_content_layout.addWidget(plot_label)
        
        scroll_content_layout.addStretch()

        scroll_area.setWidget(scroll_content_widget)

        main_layout.addWidget(scroll_area)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)