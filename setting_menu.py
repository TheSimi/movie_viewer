import os
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QFileDialog, QWidget, QScrollArea, QComboBox, QLineEdit, QSizePolicy,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from const import MOVIE_FOLDERS, SHOW_FOLDERS, CACHE_DIR, MEDIA_PLAYER, PLAY_SPEED
from utils import copy_text


class SettingsMenu(QDialog):
    def __init__(
            self,
            parent=None,
            movie_folders: str = MOVIE_FOLDERS,
            show_folders: str = SHOW_FOLDERS,
            media_player: str = MEDIA_PLAYER
        ):
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

        # ─── Media Player Row ───
        player_row = QHBoxLayout()
        player_label = QLabel("Media Player:")
        player_label.setFixedWidth(75)

        self.media_player_edit = QLineEdit()
        self.media_player_edit.setText(media_player)
        self.media_player_edit.setFixedWidth(190)
        self.media_player_edit.setReadOnly(True)
        self.media_player_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.media_player_edit.setCursorPosition(len(self.media_player_edit.text()))

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        browse_button = QPushButton("Browse")
        browse_button.setFixedWidth(100)
        browse_button.clicked.connect(self._browse_media_player)
        buttons_layout.addWidget(browse_button)

        copy_button = QPushButton("Copy")
        copy_button.setFixedWidth(80)
        copy_button.clicked.connect(lambda: copy_text(self.media_player_edit.text()))
        buttons_layout.addWidget(copy_button)

        player_row.addWidget(player_label)
        player_row.addWidget(self.media_player_edit)
        player_row.addLayout(buttons_layout)
        outer_layout.addLayout(player_row)

        # ─── Speed Row ───
        self.speed_container = QWidget()
        speed_row = QHBoxLayout()
        speed_label = QLabel("Play Speed:")
        speed_label.setFixedWidth(70)
        
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(PLAY_SPEED if PLAY_SPEED < 2 and PLAY_SPEED > 0.1 else 1.0)
        self.speed_spin.setDecimals(1)

        speed_row.addWidget(speed_label)
        speed_row.addWidget(self.speed_spin)
        self.speed_container.setLayout(speed_row)
        outer_layout.addWidget(self.speed_container)
        self._update_speed_row()

        # ─── Clear Cache Button ───
        self.open_cache_button = QPushButton("Open Cache")
        self.open_cache_button.setFixedWidth(150)
        self.open_cache_button.clicked.connect(self.open_cache_folder)
        outer_layout.addWidget(self.open_cache_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Combo box for switching types
        self.type_selector = QComboBox()
        self.type_selector.addItems(["Movies", "Shows"])
        self.type_selector.currentIndexChanged.connect(self.switch_type)
        self.type_selector.setFixedWidth(420)
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

    def _update_speed_row(self):
        exe_basename = os.path.basename(self.media_player_edit.text())
        if exe_basename == "vlc.exe":
            self.speed_container.setVisible(True)
        else:
            self.speed_container.setVisible(False)

    def _browse_media_player(self):
            path, _ = QFileDialog.getOpenFileName(self, "Select Media Player exe", "", "Executable Files (*.exe)")
            if path:
                self.media_player_edit.setText(os.path.normpath(path))
                self.media_player_edit.setCursorPosition(len(path))
                self._update_speed_row()

    @staticmethod
    def open_cache_folder():
        try:
            first_file = os.path.join(CACHE_DIR, os.listdir(CACHE_DIR)[0])
            subprocess.Popen(f'explorer /select,"{first_file}"')
        except IndexError:
            subprocess.Popen(f'explorer /select,"{CACHE_DIR}"')

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
            remove_btn.setFixedWidth(100)
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
                target_list.append(os.path.normpath(folder))
                self.update_folder_list()
