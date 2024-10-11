from typing import Optional

import debugpy
from loguru import logger
from PySide6.QtCore import QThread, Signal

from audio_backends.audio_backend import AudioBackend
from player_backends.player_backend import PlayerBackend


class PlayerThread(QThread):
    position_changed = Signal(int, int)  # Signal to emit position and length
    song_finished = Signal()  # Signal to emit when song is finished

    def __init__(
        self,
        player_backend: PlayerBackend,
        audio_backend: AudioBackend,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.player_backend: PlayerBackend = player_backend
        self.audio_backend: AudioBackend = audio_backend
        self.stop_flag: bool = False
        self.pause_flag: bool = False
        logger.debug("PlayerThread initialized")

    def run(self) -> None:
        # debugpy.debug_this_thread()
        module_length: float = self.player_backend.get_module_length()
        logger.debug("Module length: {} seconds", module_length)

        count: int = 0

        while not self.stop_flag:
            if self.pause_flag:
                self.msleep(100)  # Sleep for a short time to avoid busy-waiting
                continue

            count, buffer = self.player_backend.read_chunk(
                self.audio_backend.samplerate, self.audio_backend.buffersize
            )
            if count == 0:
                logger.debug("End of module reached")
                break
            self.audio_backend.write(buffer)

            # Emit position changed signal
            current_position: float = self.player_backend.get_position_seconds()
            self.position_changed.emit(int(current_position), int(module_length))

        self.audio_backend.stop()

        if count == 0:
            self.song_finished.emit()
            logger.debug("Song finished")

        self.player_backend.free_module()
        logger.debug("Playback stopped")

    def stop(self) -> None:
        logger.debug("Stop signal received")
        self.stop_flag = True

    def pause(self) -> None:
        self.pause_flag = not self.pause_flag
        logger.debug("Pause toggled: {}", self.pause_flag)
