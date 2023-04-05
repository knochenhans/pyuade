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
        self.setPriority(QtCore.QThread.Priority.TimeCriticalPriority)
        if self.debugger_is_active():
            debugpy.debug_this_thread()

        try:
            uade.prepare_play(self.current_song)
        except Exception as e:
            print(f'prepare_play() failed: {e}')

        while self.status == PLAYERTHREADSTATUS.PLAYING:
            try:
                if not uade.play_threaded():
                    self.status = PLAYERTHREADSTATUS.STOPPED
            except EOFError as e:
                self.status = PLAYERTHREADSTATUS.STOPPED
                print(e)
            except Exception as e:
                self.status = PLAYERTHREADSTATUS.STOPPED
                print(f'play_threaded() failed: {e}')

        uade.stop()
