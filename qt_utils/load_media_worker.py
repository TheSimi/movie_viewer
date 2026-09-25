from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal

_active_tasks: set[tuple[QThread, "LoadMediaWorker"]] = set()


class LoadMediaWorker(QObject):
    """
    A worker class that runs a task (a callable) on a separate thread and
    emits the result, so the ui thread stays responsive while media is loading.
    """

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, task: Callable[[], Any], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.task = task

    def run(self) -> None:
        try:
            result = self.task()
        except Exception as e:
            self.failed.emit(f"{e.__class__.__name__} | {e}")
            return
        self.finished.emit(result)


def run_in_background(
    task: Callable[[], Any],
    on_finished: Callable[[Any], None] | None = None,
    on_failed: Callable[[str], None] | None = None,
) -> QThread:
    """
    Run a task on a background QThread and deliver the result on the ui thread.
    """
    thread = QThread()
    worker = LoadMediaWorker(task)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    if on_finished is not None:
        worker.finished.connect(on_finished)
    if on_failed is not None:
        worker.failed.connect(on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    _active_tasks.add((thread, worker))
    thread.finished.connect(lambda: _active_tasks.discard((thread, worker)))

    thread.start()
    return thread
