import datetime
from PySide6.QtCore import QObject, Signal
from PySide6 import QtCore
from ctypes import *
from PySide6.QtWidgets import QProgressDialog
from ctypes_functions import *
import json

# Subsong of a song file


class Subsong():
    def __init__(self) -> None:
        self.nr: int = 0
        self.bytes: int = 0


# Unique reference to the actual module file, filled by data from UADE

class SongFile():
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

        self.custom: bool
        self.content: bool
        self.ext: str = ""

        self.subsongs: list[Subsong] = []

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


# Represents a specific subsong of a song as playable in the playlist

class Song():
    def __init__(self) -> None:
        self.song_file: SongFile
        self.subsong: Subsong


class Uade(QObject):
    song_end = Signal()
    current_bytes_update = Signal(int)
    song_len = 0

    buf_len = 4096
    buf = (c_char * buf_len)()

    seek_position = 0

    def __init__(self):
        super().__init__()
        libao.ao_initialize()

    # Load and scan a song file

    def get_event(self, state: c_void_p) -> uade_event:
        charbytes256 = (c_char * 256)()

        event_songend = uade_event_songend(
            happy=0, stopnow=0, tailbytes=0, reason=bytes(charbytes256))

        a = (c_ubyte * UADE_MAX_MESSAGE_SIZE)()

        size = c_size_t()

        event_data = uade_event_data(size=size, data=a)

        si = uade_subsong_info(0, 0, 0, 0)

        charbytes1024 = (c_char * 1024)()

        event_union = uade_event_union(data=event_data, msg=bytes(
            charbytes1024), songend=event_songend, subsongs=si)

        event: uade_event = uade_event(type=0, uade_event_union=event_union)

        e: int = libuade.uade_get_event(byref(event), state)

        print("event type: " + str(event.type))

        return event

    def seek(self, bytes: int) -> None:
        songinfo: uade_song_info = libuade.uade_get_song_info(
            self.state).contents

        if libuade.uade_seek_samples(UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE, self.bytes_to_samples(bytes), songinfo.subsongs.cur, self.state) != 0:
            print("Seeking failed")

    @ QtCore.Slot()
    def position_changed(self, bytes: int):
        self.seek(bytes)

    def scan_subsong(self, filename: str, subsong_nr: int) -> Subsong:

        self.state = libuade.uade_new_state(None)

        size = c_size_t()

        libuade.uade_read_file(byref(size), str.encode(filename))
        libuade.uade_play(str.encode(filename), subsong_nr, self.state)

        nbytes = 1

        last_subsongbytes = 0

        songinfo = libuade.uade_get_song_info(self.state).contents

        # last_hash: int = 0

        # Determine length of subsong

        while nbytes > 0 and songinfo.subsongs.cur == subsong_nr:
            last_subsongbytes = songinfo.subsongbytes

            nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

            # h = hash(self.buf.raw)

            # if h == last_hash:
            #     print("blabla")

            # last_hash = h

            # self.check_notifications()
            # event = self.get_event(self.state)

            # Workaround: If the song is longer than 10 min, we’re probably looping forever
            if last_subsongbytes >= 176400 * 60 * 10:
                break

        libuade.uade_cleanup_state(self.state)

        subsong = Subsong()
        subsong.nr = subsong_nr
        subsong.bytes = last_subsongbytes

        return subsong

    # Scan song file and return representation of that song

    def scan_song(self, filename: str) -> SongFile:
        # Get song info

        self.state = libuade.uade_new_state(None)

        # samplerate = libuade.uade_get_sampling_rate(self.state)

        size = c_size_t()

        libuade.uade_read_file(byref(size), str.encode(filename))
        libuade.uade_play(str.encode(filename), -1, self.state)

        songinfo: uade_song_info = libuade.uade_get_song_info(
            self.state).contents

        song = SongFile()
        song.filename = filename
        song.modulemd5 = songinfo.modulemd5.decode()
        song.formatname = songinfo.formatname.decode()
        song.modulename = songinfo.modulename.decode()
        song.modulefname = songinfo.modulefname.decode()
        song.playername = songinfo.playername.decode()
        song.playerfname = songinfo.playerfname.decode()
        song.modulebytes = songinfo.modulebytes

        if songinfo.detectioninfo:
            if songinfo.detectioninfo.custom == 1:
                song.custom = True
            else:
                song.custom = False

            if songinfo.detectioninfo.content == 1:
                song.content = True
            else:
                song.content = False

            song.ext = songinfo.detectioninfo.ext.decode()

        # Scan subsongs

        song.subsongs_min = songinfo.subsongs.min
        subsongs_max: int = songinfo.subsongs.max

        libuade.uade_cleanup_state(self.state)

        # Scan subsongs

        progress = QProgressDialog(
            "Scanning subsongs...", "Cancel", song.subsongs_min, subsongs_max + 1, None)
        progress.setWindowModality(QtCore.Qt.WindowModal)

        for s in range(song.subsongs_min, subsongs_max + 1):
            progress.setValue(s)

            if progress.wasCanceled():
                break

            song.subsongs.append(self.scan_subsong(filename, s))

        progress.setValue(subsongs_max + 1)

        return song

    def prepare_play(self, song: SongFile, subsong_nr: int) -> None:
        self.state = libuade.uade_new_state(None)

        if not self.state:
            raise Exception("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        size = c_size_t()

        libuade.uade_read_file(byref(size), str.encode(song.filename))
        libuade.uade_play(str.encode(
            song.filename), song.subsongs[subsong_nr].nr + song.subsongs_min, self.state)

        format = ao_sample_format(2 * 8, samplerate, 2, 4)

        driver = libao.ao_default_driver_id()

        self.libao_device = libao.ao_open_live(driver, byref(format), None)

    def check_notifications(self):
        notification_song_end = uade_notification_song_end(
            happy=0, stopnow=0, subsong=0, subsongbytes=0, reason=None)

        # msg = (c_char * 16384)()

        # notification_union = uade_notification_union(
        #     msg=bytes(msg), song_end=notification_song_end)

        notification_union = uade_notification_union(
            msg=None, song_end=notification_song_end)

        notification = uade_notification(
            type=0, uade_notification_union=notification_union)

        if libuade.uade_read_notification(notification, self.state) == 1:
            if notification.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_MESSAGE:
                if notification_union.msg:
                    print("Amiga message: " + notification_union.msg.decode())
            elif notification.type == UADE_NOTIFICATION_TYPE.UADE_NOTIFICATION_SONG_END:
                self.song_end.emit()

                if notification_song_end.happy != 0:
                    print("song_end.happy: " + str(notification_song_end.happy))

                if notification_song_end.stopnow != 0:
                    print("song_end.stopnow: " +
                          str(notification_song_end.stopnow))

                if notification_song_end.subsong != 0:
                    print("song_end.subsong: " +
                          str(notification_song_end.subsong))

                if notification_song_end.subsongbytes != 0:
                    print("song_end.subsongbytes: " +
                          str(notification_song_end.subsongbytes))

                if notification_song_end.reason:
                    print("song_end.reason: " + notification_song_end.reason)
            else:
                print("Unknown notification type from libuade")

            libuade.uade_cleanup_notification(notification)

    def samples_to_bytes(self, samples: int) -> int:
        return samples * 4

    def bytes_to_samples(self, bytes: int) -> int:
        return int(bytes / 4)

    def play_threaded(self):
        songinfo: uade_song_info = libuade.uade_get_song_info(
            self.state).contents

        if libuade.uade_is_seeking(self.state) == 1:
            print("Currently seeking...")

        nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

        # pa = cast(buf, POINTER(c_char * buf_len))
        # a = np.frombuffer(pa.contents, dtype=np.int16)

        if nbytes < 0:
            raise Exception("Playback error")
        # elif nbytes == 0:
            # self.song_end.emit()
            # raise EOFError("Song end")

        # total = np.append(total, a)

        # Only for RMC songs
        # print(libuade.uade_get_time_position(1, self.state))

        self.current_bytes_update.emit(songinfo.subsongbytes)
        self.check_notifications()

        if not libao.ao_play(self.libao_device, self.buf, nbytes):
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
            print("uade_stop error")

        libuade.uade_cleanup_state(self.state)

        if libao.ao_close(self.libao_device) != 1:
            print("ao_close error")

        self.state = 0
