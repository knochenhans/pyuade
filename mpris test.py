from mpris_server.adapters import MprisAdapter
from mpris_server.events import EventAdapter
from mpris_server.server import Server
from mpris_server import Metadata

# Assume you have a simple media player class with play, pause, stop, next, and previous methods
class SimpleMediaPlayer:
    def __init__(self):
        self.playing = False

    def play(self):
        self.playing = True

    def pause(self):
        self.playing = False

    def stop(self):
        self.playing = False

    def next(self):
        # Implement logic to play the next track
        pass

    def previous(self):
        # Implement logic to play the previous track
        pass

# Custom implementation of MprisAdapter
class MyAppAdapter(MprisAdapter):
    # def __init__(self, player):
    #     self.player = player
    #     super().__init__()

    def metadata(self) -> Metadata:
        metadata = Metadata()
        # Populate metadata with information about the currently playing track
        # metadata['Title'] = 'Sample Track'
        # metadata['Artist'] = 'Sample Artist'
        # metadata['Album'] = 'Sample Album'
        return metadata
    
    # def playback_status(self) -> str:
    #     return 'Playing' if self.player.playing else 'Paused'

# Custom implementation of MyAppEventHandler
class MyAppEventHandler(EventAdapter):
    # def __init__(self, root, player):
    #     self.player = player
    #     super().__init__(player=player, root=root)

    def on_app_event(self, event: str):
        # trigger DBus updates based on events in your app
        if event == 'pause':
            self.on_playpause()


    # def on_playpause(self):
    #     if self.player.playing:
    #         self.player.pause()
    #     else:
    #         self.player.play()

    # def on_stop(self):
    #     self.player.stop()

    # def on_next(self):
    #     self.player.next()

    # def on_previous(self):
    #     self.player.previous()

# Create a simple media player instance
# media_player = SimpleMediaPlayer()

# Create the MPRIS adapter and server
my_adapter = MyAppAdapter()
mpris = Server('MyMediaPlayer', adapter=my_adapter)

# Initialize app integration with MPRIS
event_handler = MyAppEventHandler(root=mpris.root, player=mpris.player)
# app.register_event_handler(event_handler)
mpris.loop()
