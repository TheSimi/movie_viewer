from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel,
    QComboBox, QSizePolicy, QGridLayout, QPushButton
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PIL.ImageQt import ImageQt

class MediaButton(QPushButton):
    def __init__(self, media):
        super().__init__()
        self.media = media

        self.setFixedSize(150, 250)
        self.setStyleSheet("border: none;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Convert PIL image to QPixmap
        qt_image = ImageQt(self.media.image.copy())
        pixmap = QPixmap.fromImage(qt_image).scaled(150, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(media.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 13px;")

        layout.addWidget(image_label)
        layout.addWidget(name_label)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.clicked.connect(self.media.play)

class MainGUIWindow(QMainWindow):
    def __init__(self, show_list, movie_list):
        super().__init__()
        self.setWindowTitle("Media Browser")
        self.setGeometry(100, 100, 1000, 800)

        self.show_list = show_list
        self.movie_list = movie_list

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["Movies", "Shows"])
        self.combo_box.setFixedWidth(690)
        self.combo_box.setFont(QFont("Arial", 14))
        self.combo_box.setStyleSheet("padding: 6px;")
        self.combo_box.currentIndexChanged.connect(self.update_display)
        outer_layout.addWidget(self.combo_box)

        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(690)
        self.scroll_area.setWidgetResizable(True)
        outer_layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)

        self.update_display()

    def update_display(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_list = self.show_list if self.combo_box.currentText() == "Shows" else self.movie_list

        for idx, media in enumerate(current_list):
            button = MediaButton(media)
            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(button, row, col)