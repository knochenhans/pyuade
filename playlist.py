from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QKeyEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QToolButton, QTreeView

from ctypes_functions import *
from uade import *


class PlaylistExport():
    '''Playlist representation for export as playlist file'''
    def __init__(self, name: str = '', songs=None, current_song=0, current_song_pos=0) -> None:
        self.name = name
        self.songs = songs
        self.current_song = current_song
        self.current_song_pos = current_song_pos


class PlaylistItem(QStandardItem):
    def __init__(self):
        super().__init__()

    def flags(self, index):
        return QtGui.Qt.NoItemFlags

    # def dropEvent(self):
    #     print('test')

    # def dragEnterEvent(self):
    #     pass


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

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.setColumnWidth(0, 20)

        # Hide left-hand space from hidden expand sign
        self.setRootIsDecorated(False)
        self.header().setMinimumSectionSize(20)


class PlaylistTabBarEdit(QtWidgets.QLineEdit):
    def __init__(self, parent, rect: QRect) -> None:
        super().__init__(parent)

        self.setGeometry(rect)
        self.textChanged.connect(parent.tabBar().rename)
        self.editingFinished.connect(parent.tabBar().editing_finished)
        self.returnPressed.connect(self.close)
        #TODO: self.inputRejected.connect(self.close)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()

        super().keyPressEvent(event)


class PlaylistTabBar(QtWidgets.QTabBar):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.edit_text = ""
        self.edit_index = 0
        self.setMovable(True)

        # self.tabBarDoubleClicked.connect(self.doubleClicked)

    @ QtCore.Slot()
    def rename(self, text) -> None:
        self.edit_text = text

    @ QtCore.Slot()
    def editing_finished(self) -> None:
        self.setTabText(self.edit_index, self.edit_text)

    # @ QtCore.Slot()
    # def doubleClicked(self, index) -> None:
    #     print("test")


class PlaylistTab(QtWidgets.QTabWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        tab_bar = PlaylistTabBar(parent)
        self.setTabBar(tab_bar)

        self.tabBarDoubleClicked.connect(self.doubleClicked)
        # self.tabBarDoubleClicked.connect(self.tabBarDoubleClicked)

        self.addtabButton = QToolButton()
        self.addtabButton.setText(' + ')
        self.setCornerWidget(self.addtabButton, Qt.TopRightCorner)

    @ QtCore.Slot()
    def doubleClicked(self, index) -> None:
        self.tabBar().edit_index = index
        edit = PlaylistTabBarEdit(self, self.tabBar().tabRect(index))
        edit.show()
        edit.setFocus()

    # def tabBarDoubleClicked(self, index):
    #     print('blabla')

    def remove_current_tab(self):
        self.removeTab(self.currentIndex())


class PlaylistModel(QStandardItemModel):
    def __init__(self, parent, length):
        super().__init__(parent, length)

    def flags(self, index):
        default_flags = super().flags(index)

        if index.isValid():
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

        return default_flags

    def dropMimeData(self, data, action, row, col, parent):
        # Prevent shifting colums
        response = super().dropMimeData(data, Qt.CopyAction, row, 0, parent)
        return response
