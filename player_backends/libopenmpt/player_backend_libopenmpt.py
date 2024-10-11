import ctypes
import sys
import warnings
from typing import Optional

from loguru import logger

sys.path.append("./libopenmpt_py")

from libopenmpt_py import libopenmpt
from player_backends.player_backend import PlayerBackend, SongMetadata


def error_callback():
    pass


def log_callback():
    pass


def print_error(
    func_name: Optional[ctypes.c_char],
    mod_err: int,
    mod_err_str: Optional[ctypes.c_char],
) -> None:
    if not func_name:
        func_name = ctypes.c_char(b"unknown function")

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            mod_err_str = None
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)
            mod_err_str = None


class PlayerBackendLibOpenMPT(PlayerBackend):
    def __init__(self) -> None:
        super().__init__()
        logger.debug("PlayerBackendLibOpenMPT initialized")

    def load_module(self, module_filename: str) -> bool:
        openmpt_log_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        openmpt_error_func = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
        )
        load_mod = libopenmpt.openmpt_module_create_from_memory2

        ctls = ctypes.c_void_p()
        error = ctypes.c_int()
        error_message = ctypes.c_char_p()

        self.module_data = open(module_filename, "rb").read()
        self.module_size = len(self.module_data)

        logger.debug("Loading module")
        self.mod = load_mod(
            self.module_data,  # const void * filedata
            self.module_size,  # size_t filesize
            openmpt_log_func(log_callback),  # openmpt_log_func logfunc
            None,  # void * loguser
            openmpt_error_func(error_callback),  # openmpt_error_func errfunc
            None,  # void * erruser
            ctypes.byref(error),  # int * error
            ctypes.byref(error_message),  # const char ** error_message
            ctls,  # const openmpt_module_initial_ctl * ctls
        )

        if not self.mod:
            logger.error("Failed to load module: {}", error_message.value)
            print_error(
                ctypes.c_char(b"openmpt_module_create_from_memory2()"),
                error.value,
                ctypes.cast(error_message, ctypes.POINTER(ctypes.c_char)).contents,
            )
            libopenmpt.openmpt_free_string(error_message)
            return False

        self.fill_module_metadata()

        return True

    def get_module_length(self) -> float:
        return libopenmpt.openmpt_module_get_duration_seconds(self.mod)

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        libopenmpt.openmpt_module_error_clear(self.mod)
        buffer = (ctypes.c_short * (buffersize * 2))()
        frame_count = libopenmpt.openmpt_module_read_interleaved_stereo(
            self.mod, samplerate, buffersize, buffer
        )
        mod_err = libopenmpt.openmpt_module_error_get_last(self.mod)
        mod_err_str = libopenmpt.openmpt_module_error_get_last_message(self.mod)
        if mod_err != libopenmpt.OPENMPT_ERROR_OK:
            logger.error("Error reading module: {}", mod_err_str)
            print_error(
                ctypes.c_char(b"openmpt_module_read_interleaved_stereo()"),
                mod_err,
                mod_err_str,
            )
            libopenmpt.openmpt_free_string(mod_err_str)
        return frame_count, bytes(buffer)

    def get_position_seconds(self) -> float:
        return libopenmpt.openmpt_module_get_position_seconds(self.mod)

    def get_module_title(self) -> Optional[str]:
        return libopenmpt.openmpt_module_get_metadata(self.mod, b"title")

    def fill_module_metadata(self):
        keys = (
            libopenmpt.openmpt_module_get_metadata_keys(self.mod)
            .decode("utf-8")
            .split(";")
        )
        for key in keys:
            key_c_char_p = ctypes.c_char_p(key.encode("utf-8"))
            value = libopenmpt.openmpt_module_get_metadata(
                self.mod, key_c_char_p
            ).decode("utf-8")
            if value != "":
                match key:
                    case "type":
                        self.song_metadata["type"] = value
                    case "type_long":
                        self.song_metadata["type_long"] = value
                    case "originaltype":
                        self.song_metadata["originaltype"] = value
                    case "originaltype_long":
                        self.song_metadata["originaltype_long"] = value
                    case "container":
                        self.song_metadata["container"] = value
                    case "container_long":
                        self.song_metadata["container_long"] = value
                    case "tracker":
                        self.song_metadata["tracker"] = value
                    case "artist":
                        self.song_metadata["artist"] = value
                    case "title":
                        self.song_metadata["title"] = value
                    case "date":
                        self.song_metadata["date"] = value
                    case "message":
                        self.song_metadata["message"] = value
                    case "message_raw":
                        self.song_metadata["message_raw"] = value
                    case "warnings":
                        self.song_metadata["warnings"] = value

    def free_module(self) -> None:
        if self.mod:
            libopenmpt.openmpt_module_destroy(self.mod)
            self.mod = None
