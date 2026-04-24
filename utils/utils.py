from PyQt6.QtWidgets import QApplication


def copy_text(text: str):
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
