from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import QCoreApplication


class OptionsGeneral(QtWidgets.QWidget):
    def __init__(self, parent, settings: QtCore.QSettings):
        super().__init__(parent)

        self.settings = settings

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        audio_group = QtWidgets.QGroupBox("Audio", self)
        audio_layout = QtWidgets.QVBoxLayout(audio_group)
        layout.addWidget(audio_group)

        hbox = QtWidgets.QHBoxLayout()
        audio_layout.addLayout(hbox)

        buffer = self.settings.value("buffer", 8192)
        self.buffer_edit = QtWidgets.QLineEdit(str(buffer), self)
        self.buffer_edit.setValidator(QIntValidator(0, 65536, self))

        buffer_label = QtWidgets.QLabel("Buffer:", self)
        buffer_label.setBuddy(self.buffer_edit)

        hbox.addWidget(buffer_label)
        hbox.addWidget(self.buffer_edit)
        hbox.addStretch()

        samplerate = self.settings.value("samplerate", 44100)
        self.samplerate_edit = QtWidgets.QLineEdit(str(samplerate), self)
        self.samplerate_edit.setValidator(QIntValidator(0, 192000, self))

        samplerate_label = QtWidgets.QLabel("Sample Rate:", self)
        samplerate_label.setBuddy(self.samplerate_edit)

        hbox.addWidget(samplerate_label)
        hbox.addWidget(self.samplerate_edit)
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

    def accept(self):
        self.general.settings.setValue("buffer", int(self.general.buffer_edit.text()))
        self.general.settings.setValue(
            "samplerate", int(self.general.samplerate_edit.text())
        )
        super().accept()
