import sys

from PySide6 import QtWidgets

from ctypes_functions import *
from mainwindow import MainWindow
from uade import *

# def on_press(key):
#     if str(key) == '<179>':
#         print("1")
#     if str(key) == '<176>':
#         print("1")
#     if str(key) == '<177>':
#         print("1")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    # listener_thread = Listener(on_press=on_press, on_release=None)
    # This is a daemon=True thread, use .join() to prevent code from exiting
    # listener_thread.start()

    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())
