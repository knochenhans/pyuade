import ctypes
import os
import sys
import math
from ctypes import *

# class xmp_context(Structure):
#     _fields_ = [
#         ("name", c_char * PATH_MAX),
#     ]

libxmp = CDLL("libxmp.so", mode=RTLD_GLOBAL)


class UserString:
    def __init__(self, seq):
        if isinstance(seq, basestring):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)

    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return long(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)

    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])

    def __getslice__(self, start, end):
        start = max(start, 0)
        end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, basestring):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))

    def __radd__(self, other):
        if isinstance(other, basestring):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)

    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__

    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())

    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))

    def count(self, sub, start=0, end=sys.maxsize):
        return self.data.count(sub, start, end)

    def decode(self, encoding=None, errors=None):  # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())

    def encode(self, encoding=None, errors=None):  # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())

    def endswith(self, suffix, start=0, end=sys.maxsize):
        return self.data.endswith(suffix, start, end)

    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))

    def find(self, sub, start=0, end=sys.maxsize):
        return self.data.find(sub, start, end)

    def index(self, sub, start=0, end=sys.maxsize):
        return self.data.index(sub, start, end)

    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal()
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric()
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)

    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))

    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))

    def partition(self, sep):
        return self.data.partition(sep)

    def replace(self, old, new, maxsplit=-1):
        return self.__class__(self.data.replace(old, new, maxsplit))

    def rfind(self, sub, start=0, end=sys.maxsize):
        return self.data.rfind(sub, start, end)

    def rindex(self, sub, start=0, end=sys.maxsize):
        return self.data.rindex(sub, start, end)

    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))

    def rpartition(self, sep):
        return self.data.rpartition(sep)

    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))

    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)

    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)

    def splitlines(self, keepends=0): return self.data.splitlines(keepends)

    def startswith(self, prefix, start=0, end=sys.maxsize):
        return self.data.startswith(prefix, start, end)

    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())

    def translate(self, *args):
        return self.__class__(self.data.translate(*args))

    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))


class MutableString(UserString):
    """mutable string objects
    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.
    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.
    A faster and better solution is to rewrite your program using lists."""

    def __init__(self, string=""):
        self.data = string

    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")

    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data):
            raise IndexError
        self.data = self.data[:index] + sub + self.data[index+1:]

    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data):
            raise IndexError
        self.data = self.data[:index] + self.data[index+1:]

    def __setslice__(self, start, end, sub):
        start = max(start, 0)
        end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start]+sub.data+self.data[end:]
        elif isinstance(sub, basestring):
            self.data = self.data[:start]+sub+self.data[end:]
        else:
            self.data = self.data[:start]+str(sub)+self.data[end:]

    def __delslice__(self, start, end):
        start = max(start, 0)
        end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]

    def immutable(self):
        return UserString(self.data)

    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, basestring):
            self.data += other
        else:
            self.data += str(other)
        return self

    def __imul__(self, n):
        self.data *= n
        return self


class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj=""):
        # if isinstance(obj, (str, unicode, UserString)):
        if isinstance(obj, (str, UserString)):
            self.data = str(obj).encode('utf-8')
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)


def ReturnString(obj, func=None, arguments=None):
    return String.from_param(obj)


class struct_xmp_channel(Structure):
    pass


struct_xmp_channel.__slots__ = [
    'pan',
    'vol',
    'flg',
]
struct_xmp_channel._fields_ = [
    ('pan', c_int),
    ('vol', c_int),
    ('flg', c_int),
]


class struct_xmp_pattern(Structure):
    pass


struct_xmp_pattern.__slots__ = [
    'rows',
    'index',
]
struct_xmp_pattern._fields_ = [
    ('rows', c_int),
    ('index', c_int * 256),
]


class struct_xmp_event(Structure):
    pass


struct_xmp_event.__slots__ = [
    'note',
    'ins',
    'vol',
    'fxt',
    'fxp',
    'f2t',
    'f2p',
    '_flag',
]
struct_xmp_event._fields_ = [
    ('note', c_ubyte),
    ('ins', c_ubyte),
    ('vol', c_ubyte),
    ('fxt', c_ubyte),
    ('fxp', c_ubyte),
    ('f2t', c_ubyte),
    ('f2p', c_ubyte),
    ('_flag', c_ubyte),
]


class struct_xmp_track(Structure):
    pass


struct_xmp_track.__slots__ = [
    'rows',
    'event',
]
struct_xmp_track._fields_ = [
    ('rows', c_int),
    ('event', struct_xmp_event * 256),
]


class struct_xmp_envelope(Structure):
    pass


struct_xmp_envelope.__slots__ = [
    'flg',
    'npt',
    'scl',
    'sus',
    'sue',
    'lps',
    'lpe',
    'data',
]
struct_xmp_envelope._fields_ = [
    ('flg', c_int),
    ('npt', c_int),
    ('scl', c_int),
    ('sus', c_int),
    ('sue', c_int),
    ('lps', c_int),
    ('lpe', c_int),
    ('data', c_short * (32 * 2)),
]


class struct_anon_1(Structure):
    pass


struct_anon_1.__slots__ = [
    'ins',
    'xpo',
]
struct_anon_1._fields_ = [
    ('ins', c_ubyte),
    ('xpo', c_byte),
]


class struct_xmp_subinstrument(Structure):
    pass


struct_xmp_subinstrument.__slots__ = [
    'vol',
    'gvl',
    'pan',
    'xpo',
    'fin',
    'vwf',
    'vde',
    'vra',
    'vsw',
    'rvv',
    'sid',
    'nna',
    'dct',
    'dca',
    'ifc',
    'ifr',
]
struct_xmp_subinstrument._fields_ = [
    ('vol', c_int),
    ('gvl', c_int),
    ('pan', c_int),
    ('xpo', c_int),
    ('fin', c_int),
    ('vwf', c_int),
    ('vde', c_int),
    ('vra', c_int),
    ('vsw', c_int),
    ('rvv', c_int),
    ('sid', c_int),
    ('nna', c_int),
    ('dct', c_int),
    ('dca', c_int),
    ('ifc', c_int),
    ('ifr', c_int),
]


class struct_xmp_instrument(Structure):
    pass


struct_xmp_instrument.__slots__ = [
    'name',
    'vol',
    'nsm',
    'rls',
    'aei',
    'pei',
    'fei',
    'map',
    'sub',
    'extra',
]
struct_xmp_instrument._fields_ = [
    ('name', c_char * 32),
    ('vol', c_int),
    ('nsm', c_int),
    ('rls', c_int),
    ('aei', struct_xmp_envelope),
    ('pei', struct_xmp_envelope),
    ('fei', struct_xmp_envelope),
    ('map', struct_anon_1 * 121),
    ('sub', POINTER(struct_xmp_subinstrument)),
    ('extra', POINTER(None)),
]


class struct_xmp_sample(Structure):
    pass


struct_xmp_sample.__slots__ = [
    'name',
    'len',
    'lps',
    'lpe',
    'flg',
    'data',
]
struct_xmp_sample._fields_ = [
    ('name', c_char * 32),
    ('len', c_int),
    ('lps', c_int),
    ('lpe', c_int),
    ('flg', c_int),
    ('data', POINTER(c_ubyte)),
]


class struct_xmp_sequence(Structure):
    pass


struct_xmp_sequence.__slots__ = [
    'entry_point',
    'duration',
]
struct_xmp_sequence._fields_ = [
    ('entry_point', c_int),
    ('duration', c_int),
]


class struct_xmp_module(Structure):
    pass


struct_xmp_module.__slots__ = [
    'name',
    'type',
    'pat',
    'trk',
    'chn',
    'ins',
    'smp',
    'spd',
    'bpm',
    'len',
    'rst',
    'gvl',
    'xxp',
    'xxt',
    'xxi',
    'xxs',
    'xxc',
    'xxo',
]
struct_xmp_module._fields_ = [
    ('name', c_char * 64),
    ('type', c_char * 64),
    ('pat', c_int),
    ('trk', c_int),
    ('chn', c_int),
    ('ins', c_int),
    ('smp', c_int),
    ('spd', c_int),
    ('bpm', c_int),
    ('len', c_int),
    ('rst', c_int),
    ('gvl', c_int),
    ('xxp', POINTER(POINTER(struct_xmp_pattern))),
    ('xxt', POINTER(POINTER(struct_xmp_track))),
    ('xxi', POINTER(struct_xmp_instrument)),
    ('xxs', POINTER(struct_xmp_sample)),
    ('xxc', struct_xmp_channel * 64),
    ('xxo', c_ubyte * 256),
]


class struct_xmp_test_info(Structure):
    pass


struct_xmp_test_info.__slots__ = [
    'name',
    'type',
]
struct_xmp_test_info._fields_ = [
    ('name', c_char * 64),
    ('type', c_char * 64),
]


class struct_xmp_module_info(Structure):
    pass


struct_xmp_module_info.__slots__ = [
    'md5',
    'vol_base',
    'mod',
    'comment',
    'num_sequences',
    'seq_data',
]
struct_xmp_module_info._fields_ = [
    ('md5', c_ubyte * 16),
    ('vol_base', c_int),
    ('mod', POINTER(struct_xmp_module)),
    ('comment', String),
    ('num_sequences', c_int),
    ('seq_data', POINTER(struct_xmp_sequence)),
]


class struct_xmp_channel_info(Structure):
    pass


struct_xmp_channel_info.__slots__ = [
    'period',
    'position',
    'pitchbend',
    'note',
    'instrument',
    'sample',
    'volume',
    'pan',
    'reserved',
    'event',
]
struct_xmp_channel_info._fields_ = [
    ('period', c_uint),
    ('position', c_uint),
    ('pitchbend', c_short),
    ('note', c_ubyte),
    ('instrument', c_ubyte),
    ('sample', c_ubyte),
    ('volume', c_ubyte),
    ('pan', c_ubyte),
    ('reserved', c_ubyte),
    ('event', struct_xmp_event),
]


class struct_xmp_frame_info(Structure):
    pass


struct_xmp_frame_info.__slots__ = [
    'pos',
    'pattern',
    'row',
    'num_rows',
    'frame',
    'speed',
    'bpm',
    'time',
    'total_time',
    'frame_time',
    'buffer',
    'buffer_size',
    'total_size',
    'volume',
    'loop_count',
    'virt_channels',
    'virt_used',
    'sequence',
    'channel_info',
]
struct_xmp_frame_info._fields_ = [
    ('pos', c_int),
    ('pattern', c_int),
    ('row', c_int),
    ('num_rows', c_int),
    ('frame', c_int),
    ('speed', c_int),
    ('bpm', c_int),
    ('time', c_int),
    ('total_time', c_int),
    ('frame_time', c_int),
    ('buffer', POINTER(None)),
    ('buffer_size', c_int),
    ('total_size', c_int),
    ('volume', c_int),
    ('loop_count', c_int),
    ('virt_channels', c_int),
    ('virt_used', c_int),
    ('sequence', c_int),
    ('channel_info', struct_xmp_channel_info * 64),
]

xmp_context = c_long
try:
    xmp_version = (String).in_dll(libxmp, 'xmp_version')
except:
    pass

xmp_context = c_long
try:
    xmp_version = (String).in_dll(libxmp, 'xmp_version')
except:
    pass

try:
    xmp_vercode = (c_uint).in_dll(libxmp, 'xmp_vercode')
except:
    pass

if hasattr(libxmp, 'xmp_create_context'):
    xmp_create_context = libxmp.xmp_create_context
    xmp_create_context.argtypes = []
    xmp_create_context.restype = xmp_context

if hasattr(libxmp, 'xmp_free_context'):
    xmp_free_context = libxmp.xmp_free_context
    xmp_free_context.argtypes = [xmp_context]
    xmp_free_context.restype = None

if hasattr(libxmp, 'xmp_test_module'):
    xmp_test_module = libxmp.xmp_test_module
    xmp_test_module.argtypes = [String, POINTER(struct_xmp_test_info)]
    xmp_test_module.restype = c_int

if hasattr(libxmp, 'xmp_load_module'):
    xmp_load_module = libxmp.xmp_load_module
    xmp_load_module.argtypes = [xmp_context, String]
    xmp_load_module.restype = c_int

if hasattr(libxmp, 'xmp_scan_module'):
    xmp_scan_module = libxmp.xmp_scan_module
    xmp_scan_module.argtypes = [xmp_context]
    xmp_scan_module.restype = None

if hasattr(libxmp, 'xmp_release_module'):
    xmp_release_module = libxmp.xmp_release_module
    xmp_release_module.argtypes = [xmp_context]
    xmp_release_module.restype = None

if hasattr(libxmp, 'xmp_start_player'):
    xmp_start_player = libxmp.xmp_start_player
    xmp_start_player.argtypes = [xmp_context, c_int, c_int]
    xmp_start_player.restype = c_int

if hasattr(libxmp, 'xmp_play_frame'):
    xmp_play_frame = libxmp.xmp_play_frame
    xmp_play_frame.argtypes = [xmp_context]
    xmp_play_frame.restype = c_int

if hasattr(libxmp, 'xmp_play_buffer'):
    xmp_play_buffer = libxmp.xmp_play_buffer
    xmp_play_buffer.argtypes = [xmp_context, POINTER(None), c_int, c_int]
    xmp_play_buffer.restype = c_int

if hasattr(libxmp, 'xmp_get_frame_info'):
    xmp_get_frame_info = libxmp.xmp_get_frame_info
    xmp_get_frame_info.argtypes = [xmp_context, POINTER(struct_xmp_frame_info)]
    xmp_get_frame_info.restype = None

if hasattr(libxmp, 'xmp_end_player'):
    xmp_end_player = libxmp.xmp_end_player
    xmp_end_player.argtypes = [xmp_context]
    xmp_end_player.restype = None

if hasattr(libxmp, 'xmp_inject_event'):
    xmp_inject_event = libxmp.xmp_inject_event
    xmp_inject_event.argtypes = [xmp_context, c_int, POINTER(struct_xmp_event)]
    xmp_inject_event.restype = None

if hasattr(libxmp, 'xmp_get_module_info'):
    xmp_get_module_info = libxmp.xmp_get_module_info
    xmp_get_module_info.argtypes = [xmp_context, POINTER(struct_xmp_module_info)]
    xmp_get_module_info.restype = None

if hasattr(libxmp, 'xmp_get_format_list'):
    xmp_get_format_list = libxmp.xmp_get_format_list
    xmp_get_format_list.argtypes = []
    xmp_get_format_list.restype = POINTER(POINTER(c_char))

if hasattr(libxmp, 'xmp_next_position'):
    xmp_next_position = libxmp.xmp_next_position
    xmp_next_position.argtypes = [xmp_context]
    xmp_next_position.restype = c_int

if hasattr(libxmp, 'xmp_prev_position'):
    xmp_prev_position = libxmp.xmp_prev_position
    xmp_prev_position.argtypes = [xmp_context]
    xmp_prev_position.restype = c_int

if hasattr(libxmp, 'xmp_set_position'):
    xmp_set_position = libxmp.xmp_set_position
    xmp_set_position.argtypes = [xmp_context, c_int]
    xmp_set_position.restype = c_int

if hasattr(libxmp, 'xmp_stop_module'):
    xmp_stop_module = libxmp.xmp_stop_module
    xmp_stop_module.argtypes = [xmp_context]
    xmp_stop_module.restype = None

if hasattr(libxmp, 'xmp_restart_module'):
    xmp_restart_module = libxmp.xmp_restart_module
    xmp_restart_module.argtypes = [xmp_context]
    xmp_restart_module.restype = None

if hasattr(libxmp, 'xmp_seek_time'):
    xmp_seek_time = libxmp.xmp_seek_time
    xmp_seek_time.argtypes = [xmp_context, c_int]
    xmp_seek_time.restype = c_int

if hasattr(libxmp, 'xmp_channel_mute'):
    xmp_channel_mute = libxmp.xmp_channel_mute
    xmp_channel_mute.argtypes = [xmp_context, c_int, c_int]
    xmp_channel_mute.restype = c_int

if hasattr(libxmp, 'xmp_channel_vol'):
    xmp_channel_vol = libxmp.xmp_channel_vol
    xmp_channel_vol.argtypes = [xmp_context, c_int, c_int]
    xmp_channel_vol.restype = c_int

if hasattr(libxmp, 'xmp_set_player'):
    xmp_set_player = libxmp.xmp_set_player
    xmp_set_player.argtypes = [xmp_context, c_int, c_int]
    xmp_set_player.restype = c_int

if hasattr(libxmp, 'xmp_get_player'):
    xmp_get_player = libxmp.xmp_get_player
    xmp_get_player.argtypes = [xmp_context, c_int]
    xmp_get_player.restype = c_int

if hasattr(libxmp, 'xmp_set_instrument_path'):
    xmp_set_instrument_path = libxmp.xmp_set_instrument_path
    xmp_set_instrument_path.argtypes = [xmp_context, String]
    xmp_set_instrument_path.restype = c_int

if hasattr(libxmp, 'xmp_load_module_from_memory'):
    xmp_load_module_from_memory = libxmp.xmp_load_module_from_memory
    xmp_load_module_from_memory.argtypes = [xmp_context, POINTER(None), c_long]
    xmp_load_module_from_memory.restype = c_int

if hasattr(libxmp, 'xmp_start_smix'):
    xmp_start_smix = libxmp.xmp_start_smix
    xmp_start_smix.argtypes = [xmp_context, c_int, c_int]
    xmp_start_smix.restype = c_int

if hasattr(libxmp, 'xmp_end_smix'):
    xmp_end_smix = libxmp.xmp_end_smix
    xmp_end_smix.argtypes = [xmp_context]
    xmp_end_smix.restype = None

if hasattr(libxmp, 'xmp_smix_play_instrument'):
    xmp_smix_play_instrument = libxmp.xmp_smix_play_instrument
    xmp_smix_play_instrument.argtypes = [xmp_context, c_int, c_int, c_int, c_int]
    xmp_smix_play_instrument.restype = c_int

if hasattr(libxmp, 'xmp_smix_play_sample'):
    xmp_smix_play_sample = libxmp.xmp_smix_play_sample
    xmp_smix_play_sample.argtypes = [xmp_context, c_int, c_int, c_int, c_int]
    xmp_smix_play_sample.restype = c_int

if hasattr(libxmp, 'xmp_smix_channel_pan'):
    xmp_smix_channel_pan = libxmp.xmp_smix_channel_pan
    xmp_smix_channel_pan.argtypes = [xmp_context, c_int, c_int]
    xmp_smix_channel_pan.restype = c_int

if hasattr(libxmp, 'xmp_smix_load_sample'):
    xmp_smix_load_sample = libxmp.xmp_smix_load_sample
    xmp_smix_load_sample.argtypes = [xmp_context, c_int, String]
    xmp_smix_load_sample.restype = c_int

if hasattr(libxmp, 'xmp_smix_release_sample'):
    xmp_smix_release_sample = libxmp.xmp_smix_release_sample
    xmp_smix_release_sample.argtypes = [xmp_context, c_int]
    xmp_smix_release_sample.restype = c_int

XMP_NAME_SIZE = 64

XMP_KEY_OFF = 129

XMP_KEY_CUT = 130

XMP_KEY_FADE = 131

XMP_FORMAT_8BIT = (1 << 0)

XMP_FORMAT_UNSIGNED = (1 << 1)

XMP_FORMAT_MONO = (1 << 2)

XMP_PLAYER_AMP = 0

XMP_PLAYER_MIX = 1

XMP_PLAYER_INTERP = 2

XMP_PLAYER_DSP = 3

XMP_PLAYER_FLAGS = 4

XMP_PLAYER_CFLAGS = 5

XMP_PLAYER_SMPCTL = 6

XMP_PLAYER_VOLUME = 7

XMP_PLAYER_STATE = 8

XMP_PLAYER_SMIX_VOLUME = 9

XMP_INTERP_NEAREST = 0

XMP_INTERP_LINEAR = 1

XMP_INTERP_SPLINE = 2

XMP_DSP_LOWPASS = (1 << 0)

XMP_DSP_ALL = XMP_DSP_LOWPASS

XMP_STATE_UNLOADED = 0

XMP_STATE_LOADED = 1

XMP_STATE_PLAYING = 2

XMP_FLAGS_VBLANK = (1 << 0)

XMP_FLAGS_FX9BUG = (1 << 1)

XMP_FLAGS_FIXLOOP = (1 << 2)

XMP_SMPCTL_SKIP = (1 << 0)

XMP_MAX_KEYS = 121

XMP_MAX_ENV_POINTS = 32

XMP_MAX_MOD_LENGTH = 256

XMP_MAX_CHANNELS = 64

XMP_MAX_SRATE = 49170

XMP_MIN_SRATE = 4000

XMP_MIN_BPM = 20

XMP_MAX_FRAMESIZE = (((5 * XMP_MAX_SRATE) * 2) / XMP_MIN_BPM)

XMP_END = 1

XMP_ERROR_INTERNAL = 2

XMP_ERROR_FORMAT = 3

XMP_ERROR_LOAD = 4

XMP_ERROR_DEPACK = 5

XMP_ERROR_SYSTEM = 6

XMP_ERROR_INVALID = 7

XMP_ERROR_STATE = 8

XMP_CHANNEL_SYNTH = (1 << 0)

XMP_CHANNEL_MUTE = (1 << 1)

XMP_ENVELOPE_ON = (1 << 0)

XMP_ENVELOPE_SUS = (1 << 1)

XMP_ENVELOPE_LOOP = (1 << 2)

XMP_ENVELOPE_FLT = (1 << 3)

XMP_ENVELOPE_SLOOP = (1 << 4)

XMP_ENVELOPE_CARRY = (1 << 5)

XMP_INST_NNA_CUT = 0

XMP_INST_NNA_CONT = 1

XMP_INST_NNA_OFF = 2

XMP_INST_NNA_FADE = 3

XMP_INST_DCT_OFF = 0

XMP_INST_DCT_NOTE = 1

XMP_INST_DCT_SMP = 2

XMP_INST_DCT_INST = 3

XMP_INST_DCA_CUT = XMP_INST_NNA_CUT

XMP_INST_DCA_OFF = XMP_INST_NNA_OFF

XMP_INST_DCA_FADE = XMP_INST_NNA_FADE

XMP_SAMPLE_16BIT = (1 << 0)

XMP_SAMPLE_LOOP = (1 << 1)

XMP_SAMPLE_LOOP_BIDIR = (1 << 2)

XMP_SAMPLE_LOOP_REVERSE = (1 << 3)

XMP_SAMPLE_LOOP_FULL = (1 << 4)

XMP_SAMPLE_SYNTH = (1 << 15)

XMP_PERIOD_BASE = 6847

xmp_channel = struct_xmp_channel
xmp_pattern = struct_xmp_pattern
xmp_event = struct_xmp_event
xmp_track = struct_xmp_track
xmp_envelope = struct_xmp_envelope
xmp_subinstrument = struct_xmp_subinstrument
xmp_instrument = struct_xmp_instrument
xmp_sample = struct_xmp_sample
xmp_sequence = struct_xmp_sequence
xmp_module = struct_xmp_module
xmp_test_info = struct_xmp_test_info
xmp_module_info = struct_xmp_module_info
xmp_channel_info = struct_xmp_channel_info
xmp_frame_info = struct_xmp_frame_info
# Begin inserted files

# Begin "interface.py"

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


def _check_range(parm, val, lower, upper):
    upper = upper - 1
    if val < lower or val > upper:
        raise LookupError(
            'Invalid {0} #{1}, valid {0} range is {2} to {3}'
            .format(parm, val, lower, upper))


class TestInfo(struct_xmp_test_info):
    pass


class FrameInfo(struct_xmp_frame_info):
    def get_buffer(self):
        buf = ctypes.cast(self.buffer, POINTER(c_int8))
        return ctypes.string_at(buf, self.buffer_size)


class ModuleInfo(struct_xmp_module_info):
    pass


class Sample(object):
    """A sound sample
    A module sample contains raw PCM data and metadata such as word size,
    length or loop points.
    """

    def __init__(self, xxs):
        self._xxs = xxs

    def __getattr__(self, n):
        return getattr(self._xxs, n)

    def get_data(self):
        buf = ctypes.cast(self.data, POINTER(c_int8))
        if self.flg & XMP_SAMPLE_16BIT:
            return ctypes.string_at(buf, self.len * 2)
        else:
            return ctypes.string_at(buf, self.len)


class SubInstrument(object):
    """A sub-instrument
    Each instrument has one or more sub-instruments that can be mapped
    to different keys.
    """

    def __init__(self, sub):
        self._sub = sub

    def __getattr__(self, n):
        return getattr(self._sub, n)


class Envelope(object):
    """An envelope 
    Each instrument has amplitude, frequency and pan envelopes.
    """

    def __init__(self, env):
        self._env = env

    def __getattr__(self, n):
        return getattr(self._env, n)

    def get_point(self, num):
        _check_range('envelope point', num, 0, self._env.npt)
        return (self._env.data[num * 2], self._env.data[num * 2 + 1])


class Instrument(object):
    """An instrument
    A module instrument contains envelope data, subinstruments and
    subinstrument mapping.
    """

    def __init__(self, xxi):
        self._xxi = xxi

    def __getattr__(self, n):
        return getattr(self._xxi, n)

    def get_envelope(self, num):
        _check_range('envelope', num, 0, 3)
        if num == Xmp.VOL_ENVELOPE:
            return Envelope(self._xxi.aei)
        elif num == Xmp.FREQ_ENVELOPE:
            return Envelope(self._xxi.fei)
        elif num == Xmp.PAN_ENVELOPE:
            return Envelope(self._xxi.pei)

    def get_subinstrument(self, num):
        _check_range('sub-instrument', num, 0, self._xxi.nsm)
        return SubInstrument(self._xxi.sub[num])

    def map_subinstrument(self, key):
        _check_range('key', key, 0, XMP_MAX_KEYS)
        return self._xxi.map[key].ins


class Player(object):

    def __init__(self, freq=44100, mode=0):
        self._freq = freq
        self._mode = mode
        self._ctx = xmp_create_context()

    def __del__(self):
        xmp_free_context(self._ctx)

    def get_context(self):
        return self._ctx

    def start(self, freq=-1, mode=-1):
        """Start playing the currently loaded module."""

        if freq < 0:
            freq = self._freq

        if mode < 0:
            mode = self._mode

        code = xmp_start_player(self._ctx, freq, mode)
        if code < 0:
            if code == -XMP_ERROR_INTERNAL:
                raise RuntimeError(Xmp._error[-code])
            elif code == -XMP_ERROR_INVALID:
                raise ValueError(
                    'Invalid sampling rate {0}Hz'.format(freq))
            elif code == -XMP_ERROR_SYSTEM:
                errno = get_errno()
                raise OSError(-code,
                              '{0}: {1}'.format(Xmp._error[-code], os.strerror(errno)))

    def end(self):
        """End module replay and release player memory."""
        xmp_end_player(self._ctx)

    def set(self, param, value):
        code = xmp_set_player(self._ctx, param, value)
        if code < 0:
            if code == XMP_ERROR_INVALID:
                raise ValueError('Invalid value {0}'.format(value))

    def get(self, param):
        return xmp_get_player(self._ctx, param)

    def inject_event(self, chn, event):
        xmp_inject_event(self._ctx, chn, event)

    @staticmethod
    def get_format_list():
        format_list = xmp_get_format_list()
        i = 0
        l = []
        while format_list[i]:
            l.append(ctypes.string_at(format_list[i]))
            i = i + 1
        return l

    def next_position(self):
        """Skip replay to the start of the next position."""
        return xmp_next_position(self._ctx)

    def prev_position(self):
        """Skip replay to the start of the previous position."""
        return xmp_prev_position(self._ctx)

    def set_position(self, num):
        """Skip replay to the start of the given position."""
        return xmp_set_position(self._ctx, num)

    def scan(self):
        """Scan the loaded module for sequences and timing."""
        xmp_scan_module(self._ctx)

    def play(self, callback, loop=False, args={}):
        fi = FrameInfo()
        self.start()
        while self.play_frame():
            self.get_frame_info(fi)
            if loop and fi.loop_count > 0:
                break
            if callback(fi, args) != True:
                break
        self.end()

    def play_frame(self):
        """Play one frame of the module."""
        return xmp_play_frame(self._ctx) == 0

    def play_buffer(self, size, loop=1, buf=None):
        if buf == None:
            buf = Xmp.create_buffer(size)
        ret = xmp_play_buffer(self._ctx, buf, size, loop)
        if ret == 0:
            return buf
        else:
            return None

    def stop(self):
        """Stop the currently playing module."""
        xmp_stop_module(self._ctx)

    def get_frame_info(self, info=FrameInfo()):
        """Retrieve current frame information."""
        xmp_get_frame_info(self._ctx, pointer(info))
        return info

    def restart(self):
        """Restart the currently playing module."""
        xmp_restart_module(self._ctx)

    def seek_time(self, time):
        """Skip replay to the specified time."""
        return xmp_seek_time(self._ctx, time)

    def channel_mute(self, chn, val):
        return xmp_channel_mute(self._ctx, chn, val)

    def channel_vol(self, chn, val):
        return xmp_channel_vol(self._ctx, chn, val)

    def set_instrument_path(self, path):
        return xmp_set_instrument_path(self._ctx, path)


class Module(object):
    """
    Our module.
    """

    def __init__(self, path, player=None):

        if player == None:
            player = Player()

        self._player = player
        self._ctx = player.get_context()

        code = xmp_load_module(self._ctx, path)
        if code < 0:
            if code == -XMP_ERROR_SYSTEM:
                errno = get_errno()
                raise IOError(-code, '{0}: {1}'
                              .format(Xmp._error[-code], os.strerror(errno)))
            else:
                raise IOError(-code, Xmp._error[-code])

        self._module_info = struct_xmp_module_info()
        xmp_get_module_info(self._ctx, pointer(self._module_info))
        self._mod = self._module_info.mod[0]

    def __del__(self):
        if Xmp.VERCODE >= 0x040000:
            if self._player.get(Xmp.PLAYER_STATE) > Xmp.STATE_UNLOADED:
                self.release()

    def __getattr__(self, n):
        return getattr(self._mod, n)

    @staticmethod
    def test(path, info=struct_xmp_test_info()):
        """Test if a file is a valid module."""
        code = xmp_test_module(path, pointer(info))

        if code == -XMP_ERROR_SYSTEM:
            errno = get_errno()
            raise IOError(-code, '{0}: {1}'
                          .format(Xmp._error[-code], os.strerror(errno)))
        elif code < 0:
            raise IOError(-code, Xmp._error[-code])

        return info

    def release(self):
        """Release all memory used by the loaded module."""
        xmp_release_module(self._ctx)

    def get_info(self, info=None):
        if info == None:
            return self._module_info
        else:
            info.__dict__.update(self._module_info.__dict__)
            return info

    def get_instrument(self, num):
        _check_range('instrument', num, 0, self.ins)
        return Instrument(self._mod.xxi[num])

    def get_sample(self, num):
        _check_range('sample', num, 0, self.smp)
        return Sample(self._mod.xxs[num])

    def get_order(self, num):
        _check_range('position', num, 0, self.len)
        return self.xxo[num]

    def get_pattern(self, num):
        _check_range('pattern', num, 0, self.pat)
        return self.xxp[num][0]

    def get_track(self, num):
        _check_range('track', num, 0, self.trk)
        return self.xxt[num][0]

    def get_event(self, pat, row, chn):
        _check_range('pattern', pat, 0, self.pat)
        _check_range('channel', chn, 0, self.chn)
        _check_range('row', row, 0, self.get_pattern(pat).rows)
        trk = self.get_pattern(pat).index[chn]
        return self.get_track(trk).event[row]

    def get_channel(self, num):
        _check_range('track', num, 0, self.chn)
        return self.xxc[num]

    def get_player(self):
        return self._player


class Xmp(object):
    """A multi format module player
    Xmp implements a full-featured module player that supports
    many different module formats including Protracker MOD, Scream
    Tracker III S3M, Fast Tracker II XM and Impulse Tracker IT modules.
    """

    # Constants

    NAME_SIZE = XMP_NAME_SIZE

    KEY_OFF = XMP_KEY_OFF
    KEY_CUT = XMP_KEY_CUT
    KEY_FADE = XMP_KEY_FADE

    FORMAT_8BIT = XMP_FORMAT_8BIT
    FORMAT_UNSIGNED = XMP_FORMAT_UNSIGNED
    FORMAT_MONO = XMP_FORMAT_MONO

    PLAYER_AMP = XMP_PLAYER_AMP
    PLAYER_MIX = XMP_PLAYER_MIX
    PLAYER_INTERP = XMP_PLAYER_INTERP
    PLAYER_DSP = XMP_PLAYER_DSP
    PLAYER_FLAGS = XMP_PLAYER_FLAGS
    PLAYER_CFLAGS = XMP_PLAYER_CFLAGS
    PLAYER_SMPCTL = XMP_PLAYER_SMPCTL
    PLAYER_VOLUME = XMP_PLAYER_VOLUME
    PLAYER_STATE = XMP_PLAYER_STATE
    PLAYER_SMIX_VOLUME = XMP_PLAYER_SMIX_VOLUME

    INTERP_NEAREST = XMP_INTERP_NEAREST
    INTERP_LINEAR = XMP_INTERP_LINEAR
    INTERP_SPLINE = XMP_INTERP_SPLINE

    DSP_LOWPASS = XMP_DSP_LOWPASS
    DSP_ALL = XMP_DSP_ALL

    STATE_UNLOADED = XMP_STATE_UNLOADED
    STATE_LOADED = XMP_STATE_LOADED
    STATE_PLAYING = XMP_STATE_PLAYING

    FLAGS_VBLANK = XMP_FLAGS_VBLANK
    FLAGS_FX9BUG = XMP_FLAGS_FX9BUG
    FLAGS_FIXLOOP = XMP_FLAGS_FIXLOOP

    SMPCTL_SKIP = XMP_SMPCTL_SKIP

    MAX_KEYS = XMP_MAX_KEYS
    MAX_ENV_POINTS = XMP_MAX_ENV_POINTS
    MAX_MOD_LENGTH = XMP_MAX_MOD_LENGTH
    MAX_CHANNELS = XMP_MAX_CHANNELS
    MAX_SRATE = XMP_MAX_SRATE
    MIN_SRATE = XMP_MIN_SRATE
    MIN_BPM = XMP_MIN_BPM
    MAX_FRAMESIZE = XMP_MAX_FRAMESIZE

    END = XMP_END
    ERROR_INTERNAL = XMP_ERROR_INTERNAL
    ERROR_FORMAT = XMP_ERROR_FORMAT
    ERROR_LOAD = XMP_ERROR_LOAD
    ERROR_DEPACK = XMP_ERROR_DEPACK
    ERROR_SYSTEM = XMP_ERROR_SYSTEM
    ERROR_INVALID = XMP_ERROR_INVALID

    CHANNEL_SYNTH = XMP_CHANNEL_SYNTH
    CHANNEL_MUTE = XMP_CHANNEL_MUTE

    ENVELOPE_ON = XMP_ENVELOPE_ON
    ENVELOPE_SUS = XMP_ENVELOPE_SUS
    ENVELOPE_LOOP = XMP_ENVELOPE_LOOP
    ENVELOPE_FLT = XMP_ENVELOPE_FLT
    ENVELOPE_SLOOP = XMP_ENVELOPE_SLOOP
    ENVELOPE_CARRY = XMP_ENVELOPE_CARRY

    INST_NNA_CUT = XMP_INST_NNA_CUT
    INST_NNA_CONT = XMP_INST_NNA_CONT
    INST_NNA_OFF = XMP_INST_NNA_OFF
    INST_NNA_FADE = XMP_INST_NNA_FADE
    INST_DCT_OFF = XMP_INST_DCT_OFF
    INST_DCT_NOTE = XMP_INST_DCT_NOTE
    INST_DCT_SMP = XMP_INST_DCT_SMP
    INST_DCT_INST = XMP_INST_DCT_INST
    INST_DCA_CUT = XMP_INST_DCA_CUT
    INST_DCA_OFF = XMP_INST_DCA_OFF
    INST_DCA_FADE = XMP_INST_DCA_FADE

    SAMPLE_16BIT = XMP_SAMPLE_16BIT
    SAMPLE_LOOP = XMP_SAMPLE_LOOP
    SAMPLE_LOOP_BIDIR = XMP_SAMPLE_LOOP_BIDIR
    SAMPLE_LOOP_REVERSE = XMP_SAMPLE_LOOP_REVERSE
    SAMPLE_LOOP_FULL = XMP_SAMPLE_LOOP_FULL
    SAMPLE_SYNTH = XMP_SAMPLE_SYNTH

    PERIOD_BASE = XMP_PERIOD_BASE

    VOL_ENVELOPE = 0
    FREQ_ENVELOPE = 1
    PAN_ENVELOPE = 2

    # Error messages

    _error = [
        "No error",
        "End of module",
        "Internal error",
        "Unknown module format",
        "Can't load module",
        "Can't decompress module",
        "System error",
        "Invalid parameter"
    ]

    VERSION = xmp_version
    VERCODE = xmp_vercode.value
    VER_MAJOR = (VERCODE & 0xff0000) >> 16
    VER_MINOR = (VERCODE & 0x00ff00) >> 8
    VER_RELEASE = VERCODE & 0x0000ff

    # Extra convenience calls

    @staticmethod
    def create_buffer(size):
        return ctypes.create_string_buffer(size)

c = libxmp.xmp_create_context()

libxmp.xmp_load_module(c, String('/home/andre/Musik/Retro/Modland_links/M3/clashing waves.it'))

list = cast(libxmp.xmp_get_format_list(), POINTER(c_char_p))

for i in list:
    if i:
        print(i.decode())
    else:
        break

