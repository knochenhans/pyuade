from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QRect
from PySide6.QtGui import QKeyEvent, QStandardItemModel
from PySide6.QtWidgets import QTreeView

from ctypes_functions import *
from uade import *


class PlaylistTreeView(QTreeView):
    def __init__(self, parent=None):
        super(PlaylistTreeView, self).__init__(parent)
        self.dropIndicatorRect = QtCore.QRect()

        # Currently playing row for this tab
        self.current_row: int = 0

        self.setDragDropMode(self.InternalMove)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setEditTriggers(self.NoEditTriggers)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # self.header().setMinimumSectionSize(32)
        self.setColumnWidth(0, 50)


class PlaylistTabBarEdit(QtWidgets.QLineEdit):
    def __init__(self, parent, rect: QRect) -> None:
        super().__init__(parent)

        self.setGeometry(rect)
        self.textChanged.connect(parent.tabBar().rename)
        self.editingFinished.connect(parent.tabBar().editing_finished)
        self.returnPressed.connect(self.close)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)


class PlaylistTabBar(QtWidgets.QTabBar):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.edit_text = ""
        self.edit_index = 0
        self.setMovable(True)

    @ QtCore.Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @ QtCore.Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)


class PlaylistTab(QtWidgets.QTabWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        tab = PlaylistTabBar(parent)
        self.setTabBar(tab)

        self.tabBarDoubleClicked.connect(self.doubleClicked)

    @ QtCore.Slot()
    def doubleClicked(self, index) -> None:
        self.tabBar().edit_index = index
        edit = PlaylistTabBarEdit(self, self.tabBar().tabRect(index))
        edit.show()
        edit.setFocus()


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent, length):
        super().__init__(parent, length)

    def flags(self, index):
        default_flags = super().flags(index)

        if index.isValid():
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled

        return default_flags
    
    def dropMimeData(self, data, action, row, col, parent):
        # Prevent shifting colums
        response = super().dropMimeData(data, QtCore.Qt.CopyAction, row, 0, parent)
        return response
