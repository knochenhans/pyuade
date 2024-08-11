from ctypes import c_char, c_size_t, c_ubyte, c_void_p, byref
import pyaudio
from PySide6 import QtCore
from PySide6.QtCore import QObject, Signal
from ctypes_functions import libuade

from ctypes_classes import (
    UADE_MAX_MESSAGE_SIZE,
    UADE_NOTIFICATION_TYPE,
    UADE_SEEK_MODE,
    uade_event,
    uade_event_data,
    uade_event_songend,
    uade_event_union,
    uade_notification,
    uade_notification_song_end,
    uade_notification_union,
    uade_song_info,
    uade_subsong_info,
)
from utils.log import LOG_TYPE, log


class SubsongData:
    def __init__(self) -> None:
        self.cur: int = 0
        self.min: int = 0
        self.def_: int = 0
        self.max: int = 0


# Unique reference to the actual module file, filled by data from UADE


class SongFile:
    def __init__(self) -> None:
        self.formatname: str = ""
        self.modulebytes: int = 0
        self.modulefname: str = ""
        self.modulemd5: str = ""
        self.modulename: str = ""
        self.filename: str = ""
        self.playerfname: str = ""
        self.playername: str = ""
        self.subsongs_min: int = 0
        self.author: str = ""
        self.duration = 0.0

        self.custom: bool
        self.content: bool
        self.ext: str = ""

        self.subsong_data: SubsongData = SubsongData()


# Subsong of a song in the playlist


class Subsong:
    def __init__(self) -> None:
        self.nr: int = 0
        self.bytes: int = 0


# Represents a specific subsong of a song as playable in the playlist


class Song:
    def __init__(self) -> None:
        self.song_file: SongFile
        self.subsong: Subsong


class Uade(QObject):
    song_end = Signal()
    # current_bytes_update = Signal(int)
    current_seconds_update = Signal(float)
    song_len = 0

    buf_len = 8192
    buf = (c_char * buf_len)()

    seek_position = 0

    def __init__(self):
        super().__init__()
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None

    def __del__(self):
        self.pyaudio.terminate()

    # Load and scan a song file

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

    # def seek(self, bytes: int) -> None:
    #     songinfo: uade_song_info = libuade.uade_get_song_info(
    #         self.state).contents

    #     if libuade.uade_seek_samples(UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE, self.bytes_to_samples(bytes), songinfo.subsongs.cur, self.state) != 0:
    #         print("Seeking failed")

    def seek_seconds(self, seconds: float) -> None:
        songinfo: uade_song_info = libuade.uade_get_song_info(self.state).contents

        if (
            libuade.uade_seek(
                UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE,
                seconds,
                songinfo.subsongs.cur,
                self.state,
            )
            != 0
        ):
            log(LOG_TYPE.ERROR, "Seeking failed")

    @QtCore.Slot()
    def position_changed(self, seconds: float):
        self.seek_seconds(seconds)

    def scan_subsong(self, song_file: SongFile, subsong_nr: int) -> Subsong:
        self.state = libuade.uade_new_state(None)

        size = c_size_t()

        ret = libuade.uade_read_file(byref(size), str.encode(song_file.filename))

        if not ret:
            raise ValueError(f"Can not read file")

        subsong = Subsong()

        match libuade.uade_play(str.encode(song_file.filename), subsong_nr, self.state):
            case -1:
                # Fatal error
                raise RuntimeError(f"Fatal error")
            case 0:
                # Not playable
                raise ValueError(f"Not playable")
            case 1:
                nbytes = 1

                last_subsongbytes = 0

                songinfo = libuade.uade_get_song_info(self.state).contents

                # last_hash: int = 0

                # Determine length of subsong

                while nbytes > 0 and songinfo.subsongs.cur == subsong_nr:
                    last_subsongbytes = songinfo.subsongbytes

                    nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

                    if nbytes < 0:
                        raise RuntimeError("Playback error.")
                    elif nbytes == 0:
                        raise EOFError("Song end.")

                    # self.check_notifications()
                    # event = self.get_event(self.state)

                    # Workaround: If the song is longer than 10 min, we’re probably looping forever
                    if last_subsongbytes >= 176400 * 60 * 10:
                        break

                libuade.uade_cleanup_state(self.state)

                subsong.nr = subsong_nr
                subsong.bytes = last_subsongbytes

        return subsong

    # Scan song file and return representation of that song

    def scan_song_file(self, filename: str) -> SongFile:
        # Get song info

        self.state = libuade.uade_new_state(None)

        # samplerate = libuade.uade_get_sampling_rate(self.state)

        size = c_size_t()

        ret = libuade.uade_read_file(byref(size), str.encode(filename))

        if not ret:
            raise ValueError(f"Can not read file {filename}")

        song_file = SongFile()

        match libuade.uade_play(str.encode(filename), -1, self.state):
            case -1:
                # Fatal error
                libuade.uade_cleanup_state(self.state)
                raise Exception
            case 0:
                # Not playable
                libuade.uade_cleanup_state(self.state)
                raise Exception
            case 1:
                songinfo: uade_song_info = libuade.uade_get_song_info(
                    self.state
                ).contents

                self.check_notifications()
                self.get_event(self.state)

                song_file.filename = filename
                song_file.modulemd5 = songinfo.modulemd5.decode(encoding="latin-1")
                song_file.formatname = songinfo.formatname.decode(encoding="latin-1")
                song_file.modulename = songinfo.modulename.decode(encoding="latin-1")
                song_file.modulefname = songinfo.modulefname.decode(encoding="latin-1")
                song_file.playername = songinfo.playername.decode(encoding="latin-1")
                song_file.playerfname = songinfo.playerfname.decode(encoding="latin-1")
                song_file.modulebytes = songinfo.modulebytes
                song_file.duration = songinfo.duration

                if songinfo.detectioninfo:
                    if songinfo.detectioninfo.custom == 1:
                        song_file.custom = True
                    else:
                        song_file.custom = False

                    if songinfo.detectioninfo.content == 1:
                        song_file.content = True
                    else:
                        song_file.content = False

                    song_file.ext = songinfo.detectioninfo.ext.decode(
                        encoding="latin-1"
                    )

                # Scan subsongs

                song_file.subsong_data.cur = songinfo.subsongs.cur
                song_file.subsong_data.min = songinfo.subsongs.min
                song_file.subsong_data.max = songinfo.subsongs.max
                song_file.subsong_data.def_ = songinfo.subsongs.def_
                libuade.uade_cleanup_state(self.state)

        return song_file

    def split_subsongs(self, song_file: SongFile) -> list[Song]:
        # libuade.uade_cleanup_state(self.state)

        songs: list[Song] = []

        if max(song_file.subsong_data.min, song_file.subsong_data.max) <= 1:
            song: Song = Song()
            song.song_file = song_file
            songs.append(song)
        else:
            # Scan for subsongs
            # progress = QProgressDialog(
            #     "Scanning subsongs...", "Cancel", song_file.subsong_data.min, song_file.subsong_data.max + 1, None)
            # progress.setWindowModality(QtCore.Qt.WindowModal)

            for s in range(song_file.subsong_data.min, song_file.subsong_data.max + 1):
                # progress.setValue(s)

                # if progress.wasCanceled():
                #     break

                subsong: Song = Song()
                subsong.song_file = song_file

                try:
                    s = self.scan_subsong(song_file, s)

                    if s:
                        subsong.subsong = s
                except:
                    log(
                        LOG_TYPE.ERROR,
                        f"Playback error while scanning, discarding song: {song_file.filename}",
                    )

                songs.append(subsong)

            # progress.setValue(song_file.subsong_data.max + 1)

        return songs

    def prepare_play(self, song: Song) -> None:
        self.state = libuade.uade_new_state(None)

        if not self.state:
            raise Exception("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        size = c_size_t()

        ret = libuade.uade_read_file(byref(size), str.encode(song.song_file.filename))

        if not ret:
            raise ValueError(f"Can not read file {song.song_file.filename}")

        subsong_nr = -1

        if hasattr(song, "subsong"):
            subsong_nr = song.subsong.nr

        match libuade.uade_play(
            str.encode(song.song_file.filename), subsong_nr, self.state
        ):
            case -1:
                # Fatal error
                libuade.uade_cleanup_state(self.state)
                raise RuntimeError
            case 0:
                # Not playable
                raise ValueError
            case 1:
                self.stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(2),
                    channels=2,
                    rate=samplerate,
                    output=True,
                )

    # Check notifications, return False when song end found

    def check_notifications(self) -> bool:
        notification_song_end = uade_notification_song_end(
            happy=0, stopnow=0, subsong=0, subsongbytes=0, reason=None
        )

        # msg = (c_char * 16384)()

        # notification_union = uade_notification_union(
        #     msg=bytes(msg), song_end=notification_song_end)

        notification_union = uade_notification_union(
            msg=None, song_end=notification_song_end
        )

        notification = uade_notification(
            type=0, uade_notification_union=notification_union
        )

        if libuade.uade_read_notification(notification, self.state) == 1:
            if notification.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_MESSAGE:
                if notification_union.msg:
                    log(
                        LOG_TYPE.INFO,
                        "Amiga message: " + notification_union.msg.decode(),
                    )
            elif notification.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_SONG_END:
                # self.song_end.emit()

                if notification_song_end.happy != 0:
                    log(
                        LOG_TYPE.INFO,
                        "song_end.happy: " + str(notification_song_end.happy),
                    )

                if notification_song_end.stopnow != 0:
                    log(
                        LOG_TYPE.INFO,
                        "song_end.stopnow: " + str(notification_song_end.stopnow),
                    )

                if notification_song_end.subsong != 0:
                    log(
                        LOG_TYPE.INFO,
                        "song_end.subsong: " + str(notification_song_end.subsong),
                    )

                if notification_song_end.subsongbytes != 0:
                    log(
                        LOG_TYPE.INFO,
                        "song_end.subsongbytes: "
                        + str(notification_song_end.subsongbytes),
                    )

                if notification_song_end.reason:
                    log(
                        LOG_TYPE.INFO,
                        "song_end.reason: " + notification_song_end.reason,
                    )

                return False
            else:
                log(LOG_TYPE.INFO, "Unknown notification type from libuade")

            libuade.uade_cleanup_notification(notification)

        return True

    def samples_to_bytes(self, samples: int) -> int:
        return samples * 4

    def bytes_to_samples(self, bytes: int) -> int:
        return int(bytes / 4)

    def play_threaded(self) -> bool:
        songinfo: uade_song_info = libuade.uade_get_song_info(self.state).contents

        if libuade.uade_is_seeking(self.state) == 1:
            log(LOG_TYPE.INFO, "Currently seeking...")

        nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

        if nbytes < 0:
            raise RuntimeError("Playback error.")
        elif nbytes == 0:
            self.song_end.emit()
            raise EOFError("Song end.")

        self.current_seconds_update.emit(songinfo.subsongbytes / 176400)
        if self.check_notifications():

            # pa = cast(buf, POINTER(c_char * buf_len))
            # a = np.frombuffer(pa.contents, dtype=np.int16)

            if nbytes < 0:
                raise RuntimeError("Playback error")
            elif nbytes == 0:
                self.song_end.emit()
                # raise EOFError("Song end")
                return False
            # else:
            # total = np.append(total, a)

            # Only for RMC songs
            # print(libuade.uade_get_time_position(1, self.state))

            try:
                if self.stream:
                    self.stream.write(frames=self.buf.raw)
            except:
                return False

        else:
            self.song_end.emit()
            return False

        # cast(buf2, POINTER(c_char))

        # sd.play(total, 44100)
        # sd.wait()

        # for x in range(100):

        #     pa = cast(buf2, POINTER(c_char * 4096))
        #     a = np.frombuffer(pa.contents, dtype=np.int16)

        # if x >= 6:
        #     for i in range(16):
        #         print(a[i], " - ", format(a[i], '#016b'))
        # total = np.append(total, a)

        # def callback(outdata, frames, time, status):
        #     data = wf.buffer_read(frames, dtype='float32')
        #     if len(data) <= 0:
        #         raise sd.CallbackAbort
        #     if len(outdata) > len(data):
        #         raise sd.CallbackAbort  # wrong obviously
        #     outdata[:] = data

        # with sd.RawOutputStream(channels=wf.channels,
        #                         callback=callback) as stream:
        #     while stream.active:
        #         continue

        return True

    def stop(self):
        # print("Stop playing")

        if libuade.uade_stop(self.state) != 0:
            log(LOG_TYPE.ERROR, "uade_stop error")

        libuade.uade_cleanup_state(self.state)

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.state = 0


uade = Uade()
