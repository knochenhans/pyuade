import debugpy
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QProgressDialog


class LoaderThread(QThread):
    finished = Signal()

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.filenames: list[str] = []

    def run(self):
        # debugpy.debug_this_thread()

        from mainwindow import MainWindow

        main_window = self.parent()

        if isinstance(main_window, MainWindow) and len(self.filenames) > 0:
            progress = QProgressDialog(
                "Scanning files...", "Cancel", 0, len(self.filenames), main_window
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)

            for i, filename in enumerate(self.filenames):
                progress.setValue(i)
                if progress.wasCanceled():
                    break

                main_window.load_file(filename)

            progress.setValue(len(self.filenames))
