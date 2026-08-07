from PyQt6.QtWidgets import QApplication


def copy_text(text: str) -> None:
    clipboard = QApplication.clipboard()
    if clipboard:
        clipboard.setText(text)
