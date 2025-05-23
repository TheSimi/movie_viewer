from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QWidget, QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt


class SettingsMenu(QDialog):
    def __init__(self, parent=None, movie_folders=None, show_folders=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(500, 500)

        self.movie_folders = movie_folders or []
        self.show_folders = show_folders or []
        self.current_type = "Movies"

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(16)

        # Combo box for switching types
        self.type_selector = QComboBox()
        self.type_selector.addItems(["Movies", "Shows"])
        self.type_selector.currentIndexChanged.connect(self.switch_type)
        self.type_selector.setFixedWidth(300)
        outer_layout.addWidget(self.type_selector, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Scroll area for folder list
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedWidth(420)
        self.scroll_area.setWidgetResizable(True)
        outer_layout.addWidget(self.scroll_area, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

        # Add folder button
        self.add_button = QPushButton("Add Folder")
        self.add_button.setFixedWidth(200)
        self.add_button.clicked.connect(self.add_folder)
        outer_layout.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Confirm button
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setFixedWidth(200)
        confirm_btn.clicked.connect(self.accept)
        outer_layout.addWidget(confirm_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.update_folder_list()

    def switch_type(self):
        self.current_type = self.type_selector.currentText()
        self.update_folder_list()

    def update_folder_list(self):
        # Clear current layout
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i).widget()
            if item:
                item.setParent(None)

        folders = self.movie_folders if self.current_type == "Movies" else self.show_folders

        for folder in folders:
            row = QHBoxLayout()
            label = QLabel(folder)
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedWidth(80)
            remove_btn.clicked.connect(lambda _, f=folder: self.remove_folder(f))
            row.addWidget(label)
            row.addStretch()
            row.addWidget(remove_btn)

            container = QWidget()
            container.setLayout(row)
            self.scroll_layout.addWidget(container)

    def remove_folder(self, folder_path):
        target_list = self.movie_folders if self.current_type == "Movies" else self.show_folders
        if folder_path in target_list:
            target_list.remove(folder_path)
            self.update_folder_list()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            target_list = self.movie_folders if self.current_type == "Movies" else self.show_folders
            if folder not in target_list:
                target_list.append(folder)
                self.update_folder_list()