import ctypes

import debugpy

from player_backends.libuade import songinfo
from player_backends.libuade.ctypes_classes import (
    UADE_BYTES_PER_FRAME,
    UADE_MAX_MESSAGE_SIZE,
    UADE_NOTIFICATION_TYPE,
    uade_config,
    uade_effect,
    uade_event,
    uade_event_data,
    uade_event_songend,
    uade_event_union,
    uade_ipc,
    uade_notification,
    uade_song,
    uade_song_info,
    uade_state,
    uade_subsong_info,
)
from player_backends.libuade.ctypes_functions import libuade
from loguru import logger

from player_backends.player_backend import PlayerBackend


class PlayerBackendLibUADE(PlayerBackend):
    def __init__(self) -> None:
        super().__init__()
        self.state_ptr: ctypes._Pointer[uade_state] = libuade.uade_new_state(None)
        self.config_ptr: ctypes._Pointer[uade_config] = libuade.uade_new_config()
        # self.config = ctypes.cast(libuade.uade_new_config(), ctypes.POINTER(uade_config))

        logger.debug("PlayerBackendUADE initialized")

    def load_module(self, module_filename: str) -> bool:
        self.module_size = ctypes.c_size_t()
        ret = libuade.uade_read_file(
            ctypes.byref(self.module_size), str.encode(module_filename)
        )

        if not ret:
            error_message = f"Could not read file {module_filename}"
            logger.error(error_message)
            return False

        ret = libuade.uade_play_from_buffer(
            None, ret, self.module_size, -1, self.state_ptr
        )

        if ret < 1:
            error_message = f"LibUADE is unable to play {module_filename}"
            logger.error(error_message)
            return False

        self.song_metadata["credits"] = songinfo.get_credits(module_filename)
        self.song_metadata["title"] = self.song_metadata["credits"]["song_title"]

        for instrument in self.song_metadata["credits"]["instruments"]:
            self.song_metadata["message"] += f"{instrument['name']}\n"

        return True

    def get_module_length(self) -> float:
        info = libuade.uade_get_song_info(self.state_ptr).contents
        bytes_per_second = UADE_BYTES_PER_FRAME * libuade.uade_get_sampling_rate(
            self.state_ptr
        )
        deciseconds = (info.subsongbytes * 10) // bytes_per_second

        if info.duration > 0:
            return info.duration
        else:
            return deciseconds / 10.0

    def get_position_seconds(self) -> float:
        info = libuade.uade_get_song_info(self.state_ptr).contents
        bytes_per_second = UADE_BYTES_PER_FRAME * libuade.uade_get_sampling_rate(
            self.state_ptr
        )
        deciseconds = (info.subsongbytes * 10) // bytes_per_second

        return deciseconds / 10.0

    def read_chunk(self, samplerate: int, buffersize: int) -> tuple[int, bytes]:
        # debugpy.debug_this_thread()
        buf = (ctypes.c_char * buffersize)()
        n = uade_notification()

        nbytes = libuade.uade_read(buf, ctypes.sizeof(buf), self.state_ptr)

        while libuade.uade_read_notification(n, self.state_ptr):
            try:
                self.handle_notification(n)
            except EOFError as e:
                logger.info("handle_notification: {}", e)
                raise e
            except RuntimeError as e:
                logger.error("handle_notification: {}", e)
                raise e
            except RuntimeWarning as e:
                logger.warning("handle_notification: {}", e)
            libuade.uade_cleanup_notification(n)

        if nbytes < 0:
            raise RuntimeError("Playback error")

        if nbytes == 0:
            # raise RuntimeWarning("Song end")
            logger.info("Song end")

        return nbytes, bytes(buf)

    def handle_notification(self, n: uade_notification) -> None:
        if n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_MESSAGE:
            raise RuntimeWarning(f"Amiga message: {n.uade_notification_union.msg}")
        elif n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_SONG_END:
            if n.uade_notification_union.song_end.happy:
                raise RuntimeWarning("Song end")
            else:
                raise RuntimeError("Bad Song end")
        else:
            raise RuntimeWarning("Unknown notification type from libuade")

    def get_event(self) -> uade_event:
        charbytes256 = (ctypes.c_char * 256)()
        event_songend = uade_event_songend(
            happy=0, stopnow=0, tailbytes=0, reason=bytes(charbytes256)
        )
        a = (ctypes.c_ubyte * UADE_MAX_MESSAGE_SIZE)()
        size = ctypes.c_size_t()
        event_data = uade_event_data(size=size, data=a)
        si = uade_subsong_info(0, 0, 0, 0)
        charbytes1024 = (ctypes.c_char * 1024)()
        event_union = uade_event_union(
            data=event_data,
            msg=bytes(charbytes1024),
            songend=event_songend,
            subsongs=si,
        )
        event = uade_event(type=0, uade_event_union=event_union)
        e = libuade.uade_get_event(ctypes.byref(event), self.state_ptr)
        logger.info("event type: {}", event.type)
        return event

    def free_module(self) -> None:
        if self.state_ptr:
            libuade.uade_cleanup_state(self.state_ptr)
            self.state_ptr = libuade.uade_new_state(None)
            logger.info("UADE instance deleted")
