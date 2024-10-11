from abc import ABC, abstractmethod
from typing import Any


class AudioBackend(ABC):
    def __init__(self, samplerate: int, buffersize: int) -> None:
        self.samplerate: int = samplerate
        self.buffersize: int = buffersize

    @abstractmethod
    def write(self, data: bytes) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_buffer(self) -> Any:
        pass
