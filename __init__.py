from construct import *
from aoc.mgz.util import *
from aoc.mgz.header.map import *
from aoc.mgz.header.ai import *
from aoc.mgz.header.lobby import *
from aoc.mgz.header.replay import *
from aoc.mgz.header.scenario import *
from aoc.mgz.header.achievements import *
from aoc.mgz.header.initial import *

"""Header is compressed"""
header = Struct("header",
	ULInt32("header_length"),
	ULInt32("chapter_address"),
	Embed(TunnelAdapter(
		String("header", lambda ctx: ctx.header_length - 8, encoding = ZlibCompressor()),
		Struct("header",
			CString("version"),
			Magic("\xf6\x28\x3c\x41"),
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