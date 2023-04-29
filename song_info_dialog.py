from PySide6 import QtWidgets
from uade import Song


class SongInfoDialog(QtWidgets.QDialog):
    def __init__(self, song: Song):
        super().__init__()

        attributes = {}

        attributes['Author'] = song.song_file.author
        attributes['Filename'] = song.song_file.filename
        attributes['Format'] = song.song_file.formatname
        attributes['Extension'] = song.song_file.ext
        attributes['Size (Bytes)'] = str(song.song_file.modulebytes)
        attributes['md5'] = song.song_file.modulemd5
        attributes['Player'] = song.song_file.playername
        attributes['Player filename'] = song.song_file.playerfname

        self.setWindowTitle('Song info')

        QBtn = QtWidgets.QDialogButtonBox.Close

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.rejected.connect(self.close)

        self.vboxlayout = QtWidgets.QVBoxLayout()

        tableWidget = QtWidgets.QTableWidget(self)
        tableWidget.setRowCount(len(attributes))
        tableWidget.setColumnCount(2)
        tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        tableWidget.horizontalHeader().hide()
        tableWidget.verticalHeader().hide()
        self.vboxlayout.addWidget(tableWidget)

        self.setLayout(self.vboxlayout)

        for idx, attribute in enumerate(attributes):
            tableWidget.setItem(idx, 0, QtWidgets.QTableWidgetItem(attribute))
            tableWidget.setItem(
                idx, 1, QtWidgets.QTableWidgetItem(attributes[attribute]))
