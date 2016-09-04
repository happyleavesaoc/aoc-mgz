from construct import *
from mgz.util import *
from mgz.header.map import *
from mgz.header.ai import *
from mgz.header.lobby import *
from mgz.header.replay import *
from mgz.header.scenario import *
from mgz.header.achievements import *
from mgz.header.initial import *

"""Header is compressed"""
header = Struct("header",
    ULInt32("header_length"),
    ULInt32("chapter_address"),
    Embed(TunnelAdapter(
        String("header", lambda ctx: ctx.header_length - 8, encoding = ZlibCompressor()),
        Struct("header",
            CString("version"),
            Const("\xf6\x28\x3c\x41"),
            ai,
            replay,
            map_info,
            initial,
            achievements,
            scenario,
            lobby,
            Terminator
            )
        ))
    )
