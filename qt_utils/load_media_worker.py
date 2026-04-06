from PyQt6.QtCore import QObject, pyqtSignal

from media_classes import Media


class LoadMediaWorker(QObject):
    """
    A worker class to load media files from a list of folders
    in the background on a separate thread
    """

    finished = pyqtSignal(list)

    def __init__(
        self,
        folder_list: list,
        file_class: Media.__class__,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.folder_list = folder_list
        self.file_class = file_class
        self._is_running = False

    def run(self):
        media_list = []
        for folder in self.folder_list:
            media_list.extend(self.file_class.from_folder(folder))
        self.finished.emit(media_list)
