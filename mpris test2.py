import dbus
import dbus.mainloop.glib
from gi.repository import GLib


def media_key_handler(event):
    # Handle the media key event here
    print("Media key pressed:", event)

# Initialize the D-Bus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

# Create a custom media player D-Bus service and object path
custom_player_service = 'org.example.CustomMediaPlayer'
custom_player_object_path = '/org/example/CustomMediaPlayer'

# Create a D-Bus object for the custom media player
bus = dbus.SessionBus()
custom_player_proxy = bus.get_object(custom_player_service, custom_player_object_path)

# Add a signal receiver for media key events
custom_player_proxy.connect_to_signal('MediaPlayerKeyPressed', media_key_handler)

# Start the GLib main loop to listen for events
loop = GLib.MainLoop()
loop.run()



# from time import sleep
# import gi

# gi.require_version('Gst', '1.0')
# from typing import List

# from gi.repository import Gst
# from mpris_server.adapters import (Metadata, Microseconds, MprisAdapter,
#                                    PlayState, RateDecimal, VolumeDecimal)
# from mpris_server.base import BEGINNING, DEFAULT_RATE, MIME_TYPES, URI, DbusObj
# from mpris_server.events import EventAdapter
# from mpris_server.server import Server

# # from htidal import GUI

# class HAdapter(MprisAdapter):
#   def get_uri_schemes(self) -> List[str]:
#     return URI

#   def get_mime_types(self) -> List[str]:
#     return MIME_TYPES

#   def can_quit(self) -> bool:
#     return True

#   def quit(self):
#   #   GUI.on_main_delete_event(GUI, 0, 0)
#     pass

#   def get_current_position(self):
#   #   try:
#   #     nan_pos = GUI.player.query_position(Gst.Format.TIME)[1]
#   #     position = float(nan_pos) / Gst.SECOND
#   #   except:
#     position = 0
#     return position

#   def next(self):
#     # GUI.on_next(GUI, 0)
#     pass

#   def previous(self):
#     # GUI.on_prev(GUI, 0)
#     pass

#   def pause(self):
#     print('inside')
#     # GUI.pause(GUI)
#     pass

#   def resume(self):
#     # GUI.resume(GUI)
#     pass

#   def stop(self):
#     # GUI.stop(GUI, 0)
#     pass

#   def play(self):
#     # GUI.play(GUI)
#     pass

#   def get_playstate(self) -> PlayState:
#     # if not GUI.playing:
#     #   if not GUI.res:
#     #       return PlayState.STOPPED
#     #   else:
#     #       return PlayState.PAUSED
#     # else:
#     return PlayState.PLAYING

#   def seek(self, time):
#     print(time)
#   #   GUI.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, time * Gst.SECOND)

#   def is_repeating(self) -> bool:
#     return False

#   def is_playlist(self) -> bool:
#     return self.can_go_next() or self.can_go_previous()

#   def set_repeating(self, val: bool):
#     pass

#   def set_loop_status(self, val: str):
#     pass

#   def get_rate(self) -> float:
#     return 1.0

#   def set_rate(self, val: float):
#     pass

#   def get_shuffle(self) -> bool:
#     return False

#   def set_shuffle(self, val: bool):
#     return False

#   def get_art_url(self, track):
#     print('Later')
#     return 'Later'

#   # def get_stream_title(self):
#   #   print('Later again')

#   def is_mute(self) -> bool:
#     return False

#   def can_go_next(self) -> bool:
#     return False

#   def can_go_previous(self) -> bool:
#     return  False

#   def can_play(self) -> bool:
#     return True

#   def can_pause(self) -> bool:
#     return True

#   def can_seek(self) -> bool:
#     return False

#   def can_control(self) -> bool:
#     return True

#   def get_stream_title(self) -> str:
#     return "Test title"

#   def metadata(self) -> dict:
#     metadata = {
#     #   "mpris:trackid": "/track/1",
#     #   "mpris:length": 0,
#     #   "mpris:artUrl": "Example",
#     #   "xesam:url": "https://google.com",
#     #   "xesam:title": "Example title",
#     #   "xesam:artist": [],
#     #   "xesam:album": "Album name",
#     #   "xesam:albumArtist": [],
#     #   "xesam:discNumber": 1,
#     #   "xesam:trackNumber": 1,
#     #   "xesam:comment": [],
#     }

#     return metadata


# class HEventHandler(EventAdapter):
#     def on_app_event(self, event: str):
#       print(f"Event received: {event}")

#       if event == 'pause':
#         self.on_playpause()

# my_adapter = HAdapter()
# mpris = Server('HTidal', adapter=my_adapter)
# event_handler = HEventHandler(mpris.player, mpris.root) # need to pass mpris.player & mpris.root
# # right here you need to pass event_handler to htidal

# mpris.loop()

# sleep(10000)
