from enum import IntEnum
import sys

import debugpy
from PySide6 import QtCore

from uade import Song, uade


class PLAYERTHREADSTATUS(IntEnum):
    PLAYING = 0,
    PAUSED = 1,
    STOPPED = 2


class PlayerThread(QtCore.QThread):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.status = PLAYERTHREADSTATUS.STOPPED
        self.current_song: Song

    def debugger_is_active(self) -> bool:
        gettrace = getattr(sys, 'gettrace', lambda: None)
        return gettrace() is not None

    def run(self):
        if self.debugger_is_active():
            debugpy.debug_this_thread()

        try:
            uade.prepare_play(self.current_song)
        except:
            print('prepare_play() failed.')

        while self.status == PLAYERTHREADSTATUS.PLAYING:
            try:
                if not uade.play_threaded():
                    self.status = PLAYERTHREADSTATUS.STOPPED
            except EOFError:
                self.status = PLAYERTHREADSTATUS.STOPPED
            except Exception:
                self.status = PLAYERTHREADSTATUS.STOPPED

        uade.stop()
