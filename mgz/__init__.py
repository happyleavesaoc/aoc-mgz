from construct import *
from mgz.util import *
from mgz.header.map_info import *
from mgz.header.ai import *
from mgz.header.lobby import *
from mgz.header.replay import *
from mgz.header.scenario import *
from mgz.header.achievements import *
from mgz.header.initial import *

import zlib
from io import BytesIO
import construct.core

class ZLPrefixed(Subconstruct):
    __slots__ = ["name", "length", "subcon"]
    def __init__(self, length, subcon):
        super(ZLPrefixed, self).__init__(subcon)
        self.length = length
    def _parse(self, stream, context, path):
        length = self.length(context)
        stream2 = BytesIO(construct.core._read_stream(stream, length))
        return self.subcon._parse(stream2, context, path)

class ZLCompressed(Tunnel):
    __slots__ = []
    def __init__(self, subcon):
        super(ZLCompressed, self).__init__(subcon)
    def _decode(self, data, context):
        return zlib.decompressobj().decompress(b'x\x9c' + data)

h2 = Struct(
    "version"/CString(encoding='latin1'),
    Const(b"\xf6\x28\x3c\x41"),
    ai,
    replay,
    map_info,
    initial,
    achievements,
    scenario,
    lobby,
    Terminated
)

"""Header is compressed"""
header = Struct(
    "header_length"/Int32ul,
    "chapter_address"/Int32ul,
    Embedded(ZLPrefixed(this.header_length - 8, ZLCompressed(h2)))
)
