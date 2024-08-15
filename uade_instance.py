from ctypes import byref, c_char, c_size_t, c_ubyte, c_void_p, sizeof

from pyaudio import Stream
from PySide6 import QtCore
from PySide6.QtCore import QObject, Signal

from ctypes_classes import (
    UADE_MAX_MESSAGE_SIZE,
    UADE_NOTIFICATION_TYPE,
    uade_event,
    uade_event_data,
    uade_event_songend,
    uade_event_union,
    uade_notification,
    uade_song_info,
    uade_subsong_info,
)
from ctypes_functions import libuade
from utils.log import LOG_TYPE, log


class uade_instance:
    def __init__(self) -> None:
        self.state = libuade.uade_new_state(None)
        self.config = libuade.uade_new_config()

        log(LOG_TYPE.INFO, "UADE instance created")

    def get_sample_rate(self) -> int:
        return libuade.uade_get_sampling_rate(self.state)

    def read_file(self, filename: str) -> tuple:
        size = c_size_t()
        ret = libuade.uade_read_file(byref(size), str.encode(filename))

        if not ret:
            raise ValueError(f"Could not read file {filename}")

        return ret, size

    def play_from_buffer(self, buffer: c_char, size: c_size_t) -> int:
        ret = libuade.uade_play_from_buffer(None, buffer, size, -1, self.state)
        return ret

    def get_song_info(self) -> uade_song_info:
        return libuade.uade_get_song_info(self.state)

    def get_config(self) -> c_void_p:
        return self.config

    def __del__(self) -> None:
        libuade.uade_cleanup_state(self.state)

        log(LOG_TYPE.INFO, "UADE instance deleted")

    def play_loop(self, stream: Stream) -> None:
        buf = (c_char * 8192)()
        n = uade_notification()

        nbytes = libuade.uade_read(buf, sizeof(buf), self.state)

        while libuade.uade_read_notification(n, self.state):
            self.handle_notification(n)
            libuade.uade_cleanup_notification(n)

        if nbytes < 0:
            raise RuntimeError("Playback error")

        if nbytes == 0:
            raise EOFError("Song end")

        self.audio_play(buf.raw, stream)

    def song_info(self) -> uade_song_info:
        return libuade.uade_get_song_info(self.state).contents

    def handle_notification(self, n: uade_notification) -> None:
        if n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_MESSAGE:
            raise RuntimeWarning(f"Amiga message: {n.uade_notification_union.msg}")
        elif n.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_SONG_END:
            if n.uade_notification_union.song_end.happy:
                raise EOFError("Song end")
            else:
                raise RuntimeError("Bad Song end")
        else:
            raise RuntimeWarning("Unknown notification type from libuade")

    def audio_play(self, samples: bytes, stream: Stream) -> None:
        stream.write(samples)

    def get_event(self, state: c_void_p) -> uade_event:
        charbytes256 = (c_char * 256)()

        event_songend = uade_event_songend(
            happy=0, stopnow=0, tailbytes=0, reason=bytes(charbytes256)
        )

        a = (c_ubyte * UADE_MAX_MESSAGE_SIZE)()

        size = c_size_t()

        event_data = uade_event_data(size=size, data=a)

        si = uade_subsong_info(0, 0, 0, 0)

        charbytes1024 = (c_char * 1024)()

        event_union = uade_event_union(
            data=event_data,
            msg=bytes(charbytes1024),
            songend=event_songend,
            subsongs=si,
        )

        event: uade_event = uade_event(type=0, uade_event_union=event_union)

        e: int = libuade.uade_get_event(byref(event), state)

        log(LOG_TYPE.INFO, f"event type: {event.type}")

        return event

    # @QtCore.Slot()
    # def position_changed(self, seconds: float):
    #     self.seek_seconds(seconds)

    # def play_from_file(self, filename):

    #     match libuade.uade_play(str.encode(filename), -1, self.state):
    #         case -1:
    #             # Fatal error
    #             libuade.uade_cleanup_state(self.state)
    #             raise RuntimeError
    #         case 0:
    #             # Not playable
    #             raise ValueError
    #         case 1:
    #             self.stream = self.pyaudio.open(
    #                 format=self.pyaudio.get_format_from_width(2),
    #                 channels=2,
    #                 rate=self.samplerate,
    #                 output=True,
    #             )

    # def uade_enable_uadecore_log_collection(self):
    #     libuade.uade_enable_uadecore_log_collection(self.state)

    #     log(LOG_TYPE.INFO, "UADE log collection enabled")

    # def print_info(self):
    #     info = self.get_song_info()
    #     uade_info_mode = True

    #     if uade_info_mode:
    #         log(LOG_TYPE.INFO, "formatname:", info.formatname)
    #         log(LOG_TYPE.INFO, "modulename:", info.modulename)
    #         log(LOG_TYPE.INFO, "playername:", info.playername)
    #         log(
    #             LOG_TYPE.INFO,
    #             "subsongs: cur",
    #             info.subsongs.cur,
    #             "min",
    #             info.subsongs.min,
    #             "max",
    #             info.subsongs.max,
    #         )
    #         log(LOG_TYPE.INFO, "modulefname:", info.modulefname)
    #         log(LOG_TYPE.INFO, "playerfname:", info.playerfname)

    #         # log(LOG_TYPE.INFO, "uade_logs:", ast.s)
    #         # z_string_free(ast)
    #     else:
    #         n = 1 + info.subsongs.max - info.subsongs.min
    #         log(LOG_TYPE.INFO, "Format name:", info.formatname)
    #         log(LOG_TYPE.INFO, "Module name:", info.modulename)
    #         log(LOG_TYPE.INFO, "Player name:", info.playername)
    #         if n > 1:
    #             log(
    #                 LOG_TYPE.INFO,
    #                 "There are",
    #                 n,
    #                 "subsongs in range [",
    #                 info.subsongs.min,
    #                 ",",
    #                 info.subsongs.max,
    #                 "].",
    #             )
