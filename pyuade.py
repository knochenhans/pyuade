import sys

from PySide6 import QtWidgets

from ctypes_functions import *
from mainwindow import MainWindow
from uade import *
import atexit

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())

def exit():
    # Kill remaining "uadecore" processes
    libuade.uade_stop(None)
    
atexit.register(exit)