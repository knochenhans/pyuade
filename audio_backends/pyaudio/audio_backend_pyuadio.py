import contextlib

from loguru import logger
from pyaudio import PyAudio, Stream, get_format_from_width

from audio_backends.audio_backend import AudioBackend


class AudioBackendPyAudio(AudioBackend):
    def __init__(self, samplerate: int = 48000, buffersize: int = 1024) -> None:
        self.samplerate: int = samplerate
        self.buffersize: int = buffersize
        self.buffer: bytes = bytes(self.buffersize * 2 * 2)

        with contextlib.redirect_stdout(None):
            self.p: PyAudio = PyAudio()
            self.stream: Stream = self.p.open(
                format=get_format_from_width(2),
                channels=2,
                rate=self.samplerate,
                output=True,
                frames_per_buffer=self.buffersize,
            )
        logger.debug(
            "PyAudio AudioBackend initialized with samplerate: {} and buffersize: {}",
            samplerate,
            buffersize,
        )

    def write(self, data: bytes) -> None:
        self.stream.write(data)

    def stop(self) -> None:
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        logger.debug("PyAudio AudioBackend stopped")

    def get_buffer(self) -> bytes:
        return self.buffer
