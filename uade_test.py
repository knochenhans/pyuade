import unittest

from uade import *


class Test(unittest.TestCase):
    def test_load_song(self):
        uade = Uade()

        song = uade.scan_song(
            "/mnt/Daten/Musik/Retro/Games/pinball dreams - ignition.mod")

        self.assertEquals(len(song.subsongs), 35)
        self.assertEquals(int(song.modulebytes), 201064)

        song = uade.scan_song(
            "/mnt/Daten/Musik/Retro/Games/pinball dreams - beatbox.mod")

        self.assertEquals(len(song.subsongs), 38)
        self.assertEquals(int(song.modulebytes), 152792)
