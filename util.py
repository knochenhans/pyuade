from enum import IntEnum
import os


class TREEVIEWCOL(IntEnum):
    FILENAME = 0
    SONGNAME = 1
    DURATION = 2
    PLAYER = 3
    PATH = 4
    SUBSONG = 5
    AUTHOR = 6


path = os.path.dirname(os.path.realpath(__file__))
