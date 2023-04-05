import sys

from PySide6 import QtWidgets

from ctypes_functions import *
from mainwindow import MainWindow
from uade import *

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())
