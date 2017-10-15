"""Entry point for reading MGZ."""

# pylint: disable=invalid-name,no-name-in-module

from construct import (Struct, CString, Const, Int32ul, Embedded, Float32l, Terminated, this)
from mgz.util import MgzPrefixed, ZlibCompressed
from mgz.header.ai import ai
from mgz.header.replay import replay
from mgz.header.map_info import map_info
from mgz.header.initial import initial
from mgz.header.achievements import achievements
from mgz.header.scenario import scenario
from mgz.header.lobby import lobby


compressed_header = Struct(
    "version"/CString(encoding='latin1'),
    "sub_version"/Float32l,
    ai,
    replay,
    map_info,
    initial,
    achievements,
    scenario,
    lobby,
    Terminated
)

subheader = Struct(
    "chapter_address"/Int32ul,
    Embedded(MgzPrefixed(this._.header_length - 8, ZlibCompressed(compressed_header)))
)

"""Header is compressed"""
header = Struct(
    "header_length"/Int32ul,
    Embedded(subheader)
)
