from enum import IntEnum
import os


class TREEVIEWCOL(IntEnum):
    PLAYING = 0
    FILENAME = 1
    SONGNAME = 2
    DURATION = 3
    PLAYER = 4
    PATH = 5
    SUBSONG = 6
    AUTHOR = 7


path = os.path.dirname(os.path.realpath(__file__))
