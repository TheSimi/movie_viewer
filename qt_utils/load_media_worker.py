import time
from PyQt6.QtCore import QObject, pyqtSignal

from media_classes import Media

class LoadMediaWorker(QObject):
    finished = pyqtSignal(list)
    
    def __init__(self, folder_list: list, file_class: Media.__class__, parent: QObject | None = None) -> None:
        super().__init__(parent)
        
        self.folder_list = folder_list
        self.file_class = file_class
    
    def run(self):
        media_list = []
        for folder in self.folder_list:
            media_list.extend(self.file_class.from_folder(folder))
        time.sleep(0.5) # simulate loading time
        self.finished.emit(media_list)