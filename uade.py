import datetime
from PySide6.QtCore import QObject, Signal
from PySide6 import QtCore
from ctypes import *
from ctypes_functions import *


class Subsong_data():
    cur: int = 0
    min: int = 0
    max: int = 0
    def_: int = 0


class Subsong():
    nr: int = 0
    bytes: int = 0


class SongFile():
    formatname: str = ""
    modulebytes: int = 0
    modulefname: str = ""
    modulemd5: str = ""
    modulename: str = ""
    filename: str = ""
    playerfname: str = ""
    playername: str = ""

    custom: bool
    content: bool
    ext: str = ""

    subsongs: Subsong

    def __init__(self) -> None:
        self.subsongs = []


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

    def get_event(self, state):
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

        event = uade_event(type=0, uade_event_union=event_union)

        e = libuade.uade_get_event(byref(event), state)

        print("event type: " + str(event.type))

        return event

    def seek(self, bytes_):
        self.seek_position = bytes_

    @ QtCore.Slot()
    def position_changed(self, bytes):
        self.seek(bytes)

    def scan_song(self, filename) -> SongFile:
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

        subsongs_min = songinfo.subsongs.min
        subsongs_max = songinfo.subsongs.max

        libuade.uade_cleanup_state(self.state)

        for s in range(subsongs_min, subsongs_max + 1):

            self.state = libuade.uade_new_state(None)

            size = c_size_t()

            libuade.uade_read_file(byref(size), str.encode(filename))
            libuade.uade_play(str.encode(filename), s, self.state)

            nbytes = 1

            last_subsongbytes = 0

            songinfo = libuade.uade_get_song_info(self.state).contents

            last_hash = 0

            while nbytes > 0 and songinfo.subsongs.cur == s:
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
            subsong.nr = s
            subsong.bytes = last_subsongbytes

            song.subsongs.append(subsong)

        return song

    def prepare_play(self, filename, subsong):
        self.state = libuade.uade_new_state(None)

        if not self.state:
            raise Exception("uade_state is NULL")

        samplerate = libuade.uade_get_sampling_rate(self.state)

        size = c_size_t()

        libuade.uade_read_file(byref(size), str.encode(filename))
        libuade.uade_play(str.encode(filename), subsong, self.state)

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

    def play_threaded(self):
        songinfo: uade_song_info = libuade.uade_get_song_info(
            self.state).contents

        if libuade.uade_is_seeking(self.state) == 1:
            print("Seeking...")

        if self.seek_position > 0:
            print(int(self.seek_position / 2 / 16))
            # if not libuade.uade_seek_samples(UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE, int(self.seek_position / 2 / 16), songinfo.subsongs.cur, self.state):
            if not libuade.uade_seek_samples(UADE_SEEK_MODE.UADE_SEEK_SUBSONG_RELATIVE, 4096 * 1000, songinfo.subsongs.cur, self.state):
                print("Seeking failed")
            # print(int(bytes_ / 2 / 16))
            self.seek_position = 0
        else:
            nbytes = libuade.uade_read(self.buf, self.buf_len, self.state)

            # pa = cast(buf, POINTER(c_char * buf_len))
            # a = np.frombuffer(pa.contents, dtype=np.int16)

            if nbytes < 0:
                raise Exception("Playback error")
            # elif nbytes == 0:
                # self.song_end.emit()
                # raise EOFError("Song end")

            # total = np.append(total, a)

            # self.check_notifications()

            # Only for RMC songs
            # print(libuade.uade_get_time_position(1, self.state))

        

            self.current_bytes_update.emit(songinfo.subsongbytes)

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
