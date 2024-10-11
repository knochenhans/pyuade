from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QCoreApplication

class OptionsGeneral(QtWidgets.QWidget):
    def __init__(self, parent, settings: QtCore.QSettings):
        super().__init__(parent)

        self.settings = settings

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        hbox = QtWidgets.QHBoxLayout()
        layout.addLayout(hbox)

        buffer = self.settings.value("buffer", 8192)
        self.buffer_edit = QtWidgets.QLineEdit(str(buffer), self)
        self.buffer_edit.setValidator(QIntValidator(0, 1000000, self))

        label = QtWidgets.QLabel("Buffer:", self)
        label.setBuddy(self.buffer_edit)

        hbox.addWidget(label)
        hbox.addWidget(self.buffer_edit)
        hbox.addStretch()


class Options(QtWidgets.QDialog):
    def __init__(self, parent, settings: QtCore.QSettings):
        super().__init__(parent)

        self.tab_widget = QtWidgets.QTabWidget()

        self.general = OptionsGeneral(self, settings)

        self.setWindowTitle(QCoreApplication.translate("Options", "dialog_options"))

        self.tab_widget.addTab(self.general, "General")
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        self.layout().addWidget(self.tab_widget)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout().addWidget(self.buttons)