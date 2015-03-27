from construct import *
from aoc.mgz.enums import *
from aoc.mgz.util import *

"""Object IDs can be looked up via Advanced Genie Editor"""

"""Existing objects all have the same header"""
existing_object_header = Struct("header",
	ObjectEnum(ULInt16("object_type")),
	Padding(2),
	Padding(4),
	LFloat32("hitpoints"),
	Padding(4),
	ULInt32("object_id"),
	Padding(1),
	LFloat32("x"),
	LFloat32("y"),
)

"""Resource-specific header

Note: these fields might exist on non-resources, but be empty (?)
"""
resource_header = Struct("resource_header",
	Embed(existing_object_header),
	Padding(12),
	ResourceEnum(SLInt16("resource_type")),
	LFloat32("amount"),
)

"""Other - seems to be items under Units > Other in the scenario editor """
other = Struct("other",
	Embed(existing_object_header),
	Padding(37)
)

"""Units - typically villagers, scout, and any sheep within LOS"""
unit = Struct("unit",
	Embed(existing_object_header),
	# Not pretty, but we don't know how to parse a unit yet (also, this only works on non-restored games)
	# This isn't a constant footer, these are actually initial values of some sort
	Find("end_of_unit", b'\xff\xff\xff\xff\x00\x00\x80\xbf\x00\x00\x80\xbf\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00', None)
)

"""Buildings - ID doesn't match Build action ID - buildings can have multiple parts"""
building = Struct("building",
	Embed(existing_object_header),
	Padding(32),
	# The following sections can be refined with further research.
	# There are clearly some patterns.
	Byte("has_extra"),
	If(lambda ctx: ctx.has_extra == 2,
		Padding(17)
	),
	Padding(16),
	Byte("has_extra2"),
	If(lambda ctx: ctx.has_extra2 == 1,
		Padding(17)
	),
	Padding(127),
	ULInt16("c1"),
	ULInt16("c2"),
	If(lambda ctx: ctx.c1 > 0,
		Struct("more",
			Array(lambda ctx: ctx._.c2, Padding(8)),
			Padding(2),
		),
	),
	Padding(274),
	Byte("num"),
	If(lambda ctx: ctx.num < 100,
		Array(lambda ctx: ctx.num, ULInt32("id2")),
	),
	Padding(93),
)

"""Mainly trees and mines"""
gaia = Struct("gaia",
	Embed(resource_header),
	Padding(14),
)

""""This type has various classes of objects, we care about the fish"""
fish = Struct("fish",
	Embed(resource_header),
	Padding(14),
	Byte("has_extra"),
	If(lambda ctx: ctx.has_extra == 2,
		Padding(17)
	),
	Padding(140),
)

"""Objects that exist on the map at the start of the recorded game"""
existing_object = Struct("objects",
	ObjectTypeEnum(Byte("type")),
	Byte("player_id"),
	Anchor("OK"),
	Embed(Switch("properties", lambda ctx: ctx.type,
		{
			"gaia": gaia,
			"unit": unit,
			"building": building,
			"fish": fish,
			"other": other
		}
	)),
	# These boundary bytes can occur in the middle of a set of objects, and at the end
	# There is probably a better way to check these
	Peek(UBInt16("extension1")),
	Peek(UBInt32("extension2")),
	If(lambda ctx: ctx.extension1 == 11 and ctx.extension2 > 720898,
		Padding(10)
	),
)

"""Default values for objects, nothing of real interest"""
default_object = Struct("default_object",
	ObjectTypeEnum(Byte("type")),
	Padding(14),
	Switch("properties", lambda ctx: ctx.type,
		{
			"gaia": Padding(24),
			"object": Padding(32),
			"fish": Padding(32),
			"other": Padding(28),
		},
		default = Find("end_of_object", b'\x21\x16', 200),
	)
)