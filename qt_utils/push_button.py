from PyQt6.QtWidgets import QPushButton

from const import FOCUSED_BUTTON_STYLESHEET, IDLE_BUTTON_STYLESHEET

ENLARGE_AMOUNT = 1.05

class PushButton(QPushButton):
    def __init__(self, *args, style_sheet="", **kwargs):
        super().__init__(*args, **kwargs)

        new_idle_style = f"{IDLE_BUTTON_STYLESHEET} {style_sheet}"
        new_hover_style = f"{FOCUSED_BUTTON_STYLESHEET} {style_sheet}"
        
        self.setStyleSheet(new_idle_style)
        
        self.enterEvent = lambda arg: self.setStyleSheet(new_hover_style) # type: ignore  # noqa: ARG005
        self.leaveEvent = lambda arg: self.setStyleSheet(new_idle_style) # type: ignore # noqa: ARG005
        self.focusInEvent = lambda arg: self.setStyleSheet(new_hover_style) # type: ignore # noqa: ARG005
        self.focusOutEvent = lambda arg: self.setStyleSheet(new_idle_style) # type: ignore # noqa: ARG005
    