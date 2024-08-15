from enum import IntEnum
import sys

import debugpy
from PySide6 import QtCore
from pyaudio import PyAudio

from uade import Song, uade
from uade_instance import uade_instance
from utils.log import log, LOG_TYPE


class STATUS(IntEnum):
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2
    FINISHED = 3


class PlayerThread(QtCore.QThread):
    song_end = QtCore.Signal()
    song_finished = QtCore.Signal()
    current_seconds_update = QtCore.Signal(float)

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.status = STATUS.STOPPED
        self.current_song: Song

    # def debugger_is_active(self) -> bool:
    #     gettrace = getattr(sys, 'gettrace', lambda: None)
    #     return gettrace() is not None

    def run(self):
        # if self.debugger_is_active():
        debugpy.debug_this_thread()

        if self.status == STATUS.PLAYING:
            self.setPriority(QtCore.QThread.Priority.HighestPriority)
            self.uade_instance = uade_instance()

            ret, size = self.uade_instance.read_file(
                self.current_song.song_file.filename
            )
            ret = self.uade_instance.play_from_buffer(ret, size)

            pyaudio = PyAudio()

            stream = pyaudio.open(
                format=pyaudio.get_format_from_width(2),
                channels=2,
                rate=self.uade_instance.get_sample_rate(),
                output=True,
            )

            while self.status == STATUS.PLAYING:
                try:
                    self.uade_instance.play_loop(stream)
                except EOFError as e:
                    log(LOG_TYPE.INFO, f"UADE Core stopped: {e}")
                    self.status = STATUS.FINISHED
                except RuntimeError as e:
                    log(LOG_TYPE.ERROR, f"UADE Core playing failed: {e}")
                    self.status = STATUS.FINISHED
                except RuntimeWarning as e:
                    log(LOG_TYPE.WARNING, f"UADE Core playing warning: {e}")

                song_info = self.uade_instance.get_song_info()
                self.current_seconds_update.emit(
                    song_info.contents.subsongbytes / 176400
                )
                # TODO: What about song_info.contents.songbytes?

            if self.status == STATUS.FINISHED:
                self.song_finished.emit()
            elif self.status == STATUS.STOPPED:
                self.song_end.emit()

            stream.stop_stream()
            stream.close()
            pyaudio.terminate()

            # try:
            #     uade.prepare_play(self.current_song)
            # except Exception as e:
            #     log(LOG_TYPE.ERROR, f'prepare_play() failed: {e}')

            # while self.status == PLAYERTHREADSTATUS.PLAYING:
            #     try:
            #         if not uade.play_threaded():
            #             self.status = PLAYERTHREADSTATUS.STOPPED
            #     except EOFError as e:
            #         self.status = PLAYERTHREADSTATUS.STOPPED
            #         print(e)
            #     except Exception as e:
            #         self.status = PLAYERTHREADSTATUS.STOPPED
            #         log(LOG_TYPE.ERROR, f'play_threaded() failed: {e}')

            # uade.stop()
