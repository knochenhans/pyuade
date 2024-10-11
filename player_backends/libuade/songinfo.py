import os
from enum import Enum
from typing import Dict, List, Union

from player_backends.libuade.ctypes_functions import libuade
from ctypes import POINTER, c_ubyte, cast, create_string_buffer
from typing import TypedDict


class UadeSongInfoType(Enum):
    UADE_MODULE_INFO = 0
    UADE_HEX_DUMP_INFO = 1
    UADE_NUMBER_OF_INFOS = 2


class InstrumentInfo(TypedDict):
    index: int
    name: str
    size: int
    vol: int
    fine: int
    lstart: int
    lsize: int


class Credits(TypedDict):
    song_title: str
    max_positions: int
    instruments: List[InstrumentInfo]
    modulename: str
    authorname: str
    specialinfo: str
    file_name: str
    file_length: str
    file_prefix: str


def asciiline(buf: bytes) -> str:
    dst = []
    for c in buf[:16]:
        if chr(c).isprintable() and not chr(c).isspace():
            dst.append(chr(c))
        else:
            dst.append(".")
    return "".join(dst)


def hexdump(filename: str, toread: int) -> str:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File {filename} not found")

    with open(filename, "rb") as f:
        buf = f.read(toread)

    if not buf:
        raise ValueError("No data read from file")

    result = []
    rb = len(buf)
    roff = 0

    while roff < rb:
        line = f"{roff:03x}:  "
        if roff + 16 > rb:
            line += "Aligned line  "
        else:
            hex_part = " ".join(f"{buf[roff + i]:02x}" for i in range(16))
            ascii_part = "".join(
                chr(buf[roff + i]) if 32 <= buf[roff + i] < 127 else "."
                for i in range(16)
            )
            line += f"{hex_part[:23]}  {hex_part[24:]}  |{ascii_part}|"
        result.append(line)
        roff += 16

    return "\n".join(result)


def find_tag(buf: bytes, startoffset: int, buflen: int, tag: bytes) -> int:
    if startoffset >= buflen:
        return -1

    taglen = len(tag)
    for i in range(startoffset, buflen - taglen + 1):
        if buf[i : i + taglen] == tag:
            return i
    return -1


def string_checker(buf: bytes, off: int, maxoff: int) -> bool:
    if maxoff <= 0:
        raise ValueError("maxoff must be greater than 0")

    while off < maxoff:
        if buf[off] == 0:
            return True
        off += 1
    return False


def process_WTWT_mod(
    credits: Credits,
    buf: bytes,
    lo: bytes,
    hi: bytes,
    rel: int,
) -> None:
    len_buf = len(buf)
    offset = find_tag(buf, 0, len_buf, lo)
    if offset == -1:
        raise ValueError("Magic ID not found")

    offset = find_tag(buf, offset + 4, len_buf, hi)
    if offset == -1:
        raise ValueError("Second tag not found")

    chunk = offset - 8
    offset += rel

    if chunk < len_buf and offset < len_buf:
        txt_offset = int.from_bytes(buf[offset : offset + 4], "big") + chunk
        if txt_offset < len_buf and txt_offset != chunk:
            if not string_checker(buf, txt_offset, len_buf):
                raise ValueError("Invalid string at MODULENAME")
            credits["modulename"] = (
                buf[txt_offset:].split(b"\x00", 1)[0].decode("cp1251")
            )

        txt_offset = int.from_bytes(buf[offset + 4 : offset + 8], "big") + chunk
        if txt_offset < len_buf and txt_offset != chunk:
            if not string_checker(buf, txt_offset, len_buf):
                raise ValueError("Invalid string at AUTHORNAME")
            credits["authorname"] = (
                buf[txt_offset:].split(b"\x00", 1)[0].decode("cp1251")
            )

        txt_offset = int.from_bytes(buf[offset + 8 : offset + 12], "big") + chunk
        if txt_offset < len_buf and txt_offset != chunk:
            if not string_checker(buf, txt_offset, len_buf):
                raise ValueError("Invalid string at SPECIALINFO")
            credits["specialinfo"] = (
                buf[txt_offset:].split(b"\x00", 1)[0].decode("cp1251")
            )
    else:
        raise ValueError("Invalid chunk or offset")


def process_ahx_mod(credits: Credits, buf: bytes) -> None:
    if len(buf) < 13:
        raise ValueError("Buffer too short for AHX module")

    offset = int.from_bytes(buf[4:6], "big")

    if offset >= len(buf):
        raise ValueError("Offset out of range")

    if not string_checker(buf, offset, len(buf)):
        raise ValueError("Invalid string at song title")

    credits["song_title"] = buf[offset:].split(b"\x00", 1)[0].decode("cp1251")

    instrument_names: List[InstrumentInfo] = []
    for i in range(buf[12]):
        if not string_checker(buf, offset, len(buf)):
            break
        offset = offset + 1 + len(buf[offset:].split(b"\x00", 1)[0])
        if offset < len(buf):
            instrument_names.append(
                InstrumentInfo(
                    index=i + 1,
                    name=buf[offset:].split(b"\x00", 1)[0].decode("cp1251"),
                    size=0,
                    vol=0,
                    fine=0,
                    lstart=0,
                    lsize=0,
                )
            )

    credits["instruments"] = instrument_names


def process_ptk_mod(
    credits: Credits,
    inst: int,
    buf: bytes,
) -> None:
    if not string_checker(buf, 0, len(buf)):
        raise ValueError("Invalid string at song title")

    credits["song_title"] = buf[:20].split(b"\x00", 1)[0].decode("cp1251")

    if inst == 31:
        if len(buf) >= 0x43C:
            credits["max_positions"] = buf[0x3B6]
    else:
        if len(buf) >= 0x1DA:
            credits["max_positions"] = buf[0x1D6]

    inst_info: List[InstrumentInfo] = []
    if len(buf) >= (0x14 + inst * 0x1E):
        for i in range(inst):
            if not string_checker(buf, 0x14 + i * 0x1E, len(buf)):
                break
            name = (
                buf[0x14 + (i * 0x1E) : 0x14 + (i * 0x1E) + 22]
                .split(b"\x00", 1)[0]
                .decode("cp1251")
            )
            size = int.from_bytes(buf[42 + i * 0x1E : 44 + i * 0x1E], "big") * 2
            vol = buf[45 + i * 0x1E]
            fine = buf[44 + i * 0x1E]
            lstart = int.from_bytes(buf[46 + i * 0x1E : 48 + i * 0x1E], "big") * 2
            lsize = int.from_bytes(buf[48 + i * 0x1E : 50 + i * 0x1E], "big") * 2
            inst_info.append(
                InstrumentInfo(
                    index=i + 1,
                    name=name,
                    size=size,
                    vol=vol,
                    fine=fine,
                    lstart=lstart,
                    lsize=lsize,
                )
            )
    credits["instruments"] = inst_info


def process_digi_mod(credits: Credits, buf: bytes) -> None:
    if len(buf) < (642 + 0x30 * 0x1E):
        raise ValueError("Buffer too short for DigiBooster module")

    if not string_checker(buf, 610, len(buf)):
        raise ValueError("Invalid string at song title")

    credits["song_title"] = buf[610:].split(b"\x00", 1)[0].decode("cp1251")
    credits["max_positions"] = buf[47]

    inst_info: List[InstrumentInfo] = []
    if len(buf) >= (642 + 0x1F * 0x1E):
        for i in range(0x1F):
            if not string_checker(buf, 642 + i * 0x1E, len(buf)):
                break
            name = (
                buf[642 + (i * 0x1E) : 642 + (i * 0x1E) + 30]
                .split(b"\x00", 1)[0]
                .decode("cp1251")
            )
            size = int.from_bytes(buf[176 + i * 4 : 180 + i * 4], "big")
            vol = buf[548 + i]
            fine = buf[579 + i]
            lstart = int.from_bytes(buf[300 + i * 4 : 304 + i * 4], "big")
            lsize = int.from_bytes(buf[424 + i * 4 : 428 + i * 4], "big")
            inst_info.append(
                InstrumentInfo(
                    index=i + 1,
                    name=name,
                    size=size,
                    vol=vol,
                    fine=fine,
                    lstart=lstart,
                    lsize=lsize,
                )
            )
    credits["instruments"] = inst_info


def process_custom(credits: Credits, buf: bytes) -> None:
    if len(buf) < 4:
        raise ValueError("Buffer too short for custom module")

    if int.from_bytes(buf[:4], "big") != 0x000003F3:
        raise ValueError("Invalid custom module header")

    startpattern = b"\x70\xff\x4e\x75"
    i = find_tag(buf, 0, len(buf), startpattern)
    if i == -1 or (i + 12) >= len(buf):
        raise ValueError("Start pattern not found or out of range")

    if buf[i + 4 : i + 12] not in [b"DELIRIUM", b"EPPLAYER"]:
        raise ValueError("Invalid custom module tag")

    hunk = buf[i:]
    hunk_size = len(buf) - i

    if 16 + i + 5 >= hunk_size:
        raise ValueError("Hunk size too small")

    if hunk[16:21] == b"$VER:":
        offset = 21
        while offset < hunk_size and hunk[offset] == b" ":
            offset += 1
        if offset >= hunk_size:
            raise ValueError("Invalid version string")

        version_end = hunk[offset:].find(b"\x00")
        if version_end == -1:
            raise ValueError("Invalid version string termination")

        credits["specialinfo"] = hunk[offset : offset + version_end].decode("cp1251")

    offset = int.from_bytes(hunk[12:16], "big")
    if offset < 0:
        raise ValueError("Invalid offset in custom module")

    tag_table = hunk[offset:]
    if tag_table >= buf[len(buf) :]:
        raise ValueError("Tag table out of range")

    table_size = len(tag_table) // 8
    if table_size <= 0:
        raise ValueError("Invalid tag table size")

    for i in range(0, table_size, 2):
        x = int.from_bytes(tag_table[4 * i : 4 * (i + 1)], "big")
        y = int.from_bytes(tag_table[4 * (i + 1) : 4 * (i + 2)], "big")

        if x == 0:
            break

        if x == 0x8000445A:
            if y >= hunk_size:
                raise ValueError("Credit offset out of range")
            credit_end = hunk[y:].find(b"\x00")
            if credit_end == -1:
                raise ValueError("Invalid credit string termination")
            credits["authorname"] = hunk[y : y + credit_end].decode("cp1251")


def process_dm2_mod(credits: Credits, buf: bytes) -> None:
    if not string_checker(buf, 0x148, len(buf)):
        raise ValueError("Invalid string at remarks")
    credits["specialinfo"] = buf[0x148:].split(b"\x00", 1)[0].decode("cp1251")


def process_module(
    filename: str,
) -> Credits:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File {filename} not found")

    with open(filename, "rb") as f:
        buf = f.read()

    modfilelen = len(buf)
    credits: Credits = {
        "song_title": "",
        "max_positions": 0,
        "instruments": [],
        "modulename": "",
        "authorname": "",
        "specialinfo": "",
        "file_name": filename,
        "file_length": f"{modfilelen} bytes",
        "file_prefix": "",
    }

    pre = create_string_buffer(11)

    buf_ctype = (c_ubyte * modfilelen).from_buffer_copy(buf)
    buf_ptr = cast(buf_ctype, POINTER(c_ubyte))
    libuade.uade_filemagic(
        buf_ptr, modfilelen, pre, modfilelen, filename.encode("cp1251"), 0
    )

    pre_str = pre.value.decode("cp1251")

    credits["file_prefix"] = f"{pre_str}.*"

    if pre_str == "CUST":
        process_custom(credits, buf)
    elif pre_str == "DM2":
        process_dm2_mod(credits, buf)
    elif pre_str == "DIGI":
        process_digi_mod(credits, buf)
    elif pre_str in ["AHX", "THX"]:
        process_ahx_mod(credits, buf)
    elif pre_str in ["MOD15", "MOD15_UST", "MOD15_MST", "MOD15_ST-IV"]:
        process_ptk_mod(credits, 15, buf)
    elif pre_str in [
        "MOD",
        "MOD_DOC",
        "MOD_NTK",
        "MOD_NTK1",
        "MOD_NTK2",
        "MOD_FLT4",
        "MOD_FLT8",
        "MOD_ADSC4",
        "MOD_ADSC8",
        "MOD_COMP",
        "MOD_NTKAMP",
        "PPK",
        "MOD_PC",
        "ICE",
        "ADSC",
    ]:
        process_ptk_mod(credits, 31, buf)
    elif pre == "DL":
        process_WTWT_mod(credits, buf, b"UNCL", b"EART", 0x28)
    elif pre == "BSS":
        process_WTWT_mod(credits, buf, b"BEAT", b"HOVE", 0x1C)
    elif pre == "GRAY":
        process_WTWT_mod(credits, buf, b"FRED", b"GRAY", 0x10)
    elif pre == "JMF":
        process_WTWT_mod(credits, buf, b"J.FL", b"OGEL", 0x14)
    elif pre == "SPL":
        process_WTWT_mod(credits, buf, b"!SOP", b"ROL!", 0x10)
    elif pre == "HD":
        process_WTWT_mod(credits, buf, b"H.DA", b"VIES", 24)
    elif pre == "RIFF":
        process_WTWT_mod(credits, buf, b"RIFF", b"RAFF", 0x14)
    elif pre == "FP":
        process_WTWT_mod(credits, buf, b"F.PL", b"AYER", 0x8)
    elif pre == "CORE":
        process_WTWT_mod(credits, buf, b"S.PH", b"IPPS", 0x20)
    elif pre == "BDS":
        process_WTWT_mod(credits, buf, b"DAGL", b"ISH!", 0x14)
    else:
        raise ValueError(f"Unknown file prefix: {pre}")

    return credits


# def uade_song_info(filename: str, info_type: UadeSongInfoType) -> Credits | str:
#     if info_type == UadeSongInfoType.UADE_MODULE_INFO:
#         return process_module(filename)
#     elif info_type == UadeSongInfoType.UADE_HEX_DUMP_INFO:
#         return hexdump(filename, 2048)
#     else:
#         raise ValueError("Illegal info requested")

def get_credits(filename: str) -> Credits:
    return process_module(filename)