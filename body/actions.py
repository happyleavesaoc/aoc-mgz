from construct import *
from aoc.mgz.body.achievements import *
from aoc.mgz.enums import *

"""Not all actions are defined, not all actions are complete"""

attack = Struct("attack",
	Byte("player_id"),
	Magic("\x00\x00"),
	ULInt32("target_id"),
	ULInt32("selected"),
	LFloat32("x"),
	LFloat32("y"),
	If(lambda ctx: ctx.selected < 0xff,
		Array(lambda ctx: ctx.selected, ULInt32("unit_ids")),
	)
)

move = Struct("move",
	Byte("player_id"),
	Magic("\x00\x00"),
	Padding(4),
	ULInt32("selected"),
	LFloat32("x"),
	LFloat32("y"),
	If(lambda ctx: ctx.selected < 0xff,
		Array(lambda ctx: ctx.selected, ULInt32("unit_ids")),
	)
)

resign = Struct("resign",
	Byte("player_id"),
	Byte("player_num"),
	Flag("disconnected")
)

train = Struct("train",
	Padding(3),
	ULInt32("building_id"),
	ULInt16("unit_type"),
	ULInt16("number"),
)

research = Struct("research",
	Padding(3),
	ULInt32("building_id"),
	ULInt16("player_id"),
	ULInt16("technology_type"),
	Padding(4),
)

sell = Struct("sell",
	Byte("player_id"),
	ResourceEnum(Byte("resource_type")),
	Byte("amount"),
	Padding(4)
)

buy = Struct("buy",
	Byte("player_id"),
	ResourceEnum(Byte("resource_type")),
	Byte("amount"),
	Padding(4)
)

stop = Struct("stop",
    Byte("selected"),
    Array(lambda ctx: ctx.selected, ULInt32("object_ids"))
)

stance = Struct("stance",
    Byte("selected"),
    Byte("stance_type"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

guard = Struct("guard",
    Byte("selected"),
    Padding(2),
    ULInt32("guarded_unit_id"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

follow = Struct("follow",
    Byte("selected"),
    Padding(2),
    ULInt32("followed_unit_id"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

formation = Struct("formation",
    Byte("selected"),
    ULInt16("player_id"),
    ULInt32("formation_type"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

multiplayersave = Struct("multiplayersave",
    ULInt16("player_id"),
    Padding(5),
    CString("filename")
)

build = Struct("build",
    Byte("selected"),
    ULInt16("player_id"),
    LFloat32("x"),
    LFloat32("y"),
    BuildingEnum(ULInt32("building_type")),
    Padding(8),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

gamespeed = Struct("gamespeed",
    Padding(15),
)

wall = Struct("wall",
    Byte("selected"),
    Byte("player_id"),
    Padding(4),
    Padding(1),
    ULInt32("building_id"),
    Padding(4),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids")),
)

delete = Struct("delete",
    Padding(3),
    ULInt32("object_id"),
    ULInt32("player_id")
)

attackground = Struct("attackground",
    Byte("selected"),
    Padding(2),
    LFloat32("x"),
    LFloat32("y"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

tribute = Struct("tribute",
    Byte("player_id"),
    Byte("player_id_to"),
    ResourceEnum(Byte("resource_type")),
    LFloat32("amount"),
    LFloat32("fee")
)

unload = Struct("unload",
    ULInt16("selected"),
    Padding(1),
    LFloat32("x"), # -1 if none
    LFloat32("y"), # -1 if none
    Padding(4),
    Padding(4), # 0xffffffff
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

flare = Struct("flare",
    Padding(7),
    Array(9, Byte("player_ids")),
    Padding(3),
    LFloat32("x"),
    LFloat32("y"),
    Byte("player_id"),
    Byte("player_number"),
    Padding(2)
)

garrison = Struct("garrison",
    Byte("selected"),
    Padding(2),
    SLInt32("building_id"), # -1 cancels production queue
    ULInt32("u0"),
    LFloat32("x"),
    LFloat32("y"),
    Padding(4), # const
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids")),
)

gatherpoint = Struct("gatherpoint",
    Byte("selected"),
    Padding(2),
    ULInt32("target_id"),
    ULInt32("target_type"),
    LFloat32("x"),
    LFloat32("y"),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids"))
)

townbell = Struct("townbell",
    Padding(3),
    ULInt32("towncenter_id"),
    ULInt32("active")
)

"""Patrol

10 X-coordinates followed by 10 Y-coordinates
First of each is popped off for consistency with other actions
"""
patrol = Struct("patrol",
    Byte("selected"),
    ULInt16("waypoints"),
    LFloat32("x"),
    Array(9, LFloat32("x_more")),
    LFloat32("y"),
    Array(9, LFloat32("y_more")),
    Array(lambda ctx: ctx.selected, ULInt32("unit_ids")),
)

backtowork = Struct("backtowork",
    Padding(3),
    ULInt32("towncenter_id")
)

postgame = Struct("achievements",
	Padding(3),
	String("scenario_filename", 32, padchar = '\x00', trimdir = 'right'),
	Byte("player_num"),
	Byte("computer_num"),
	Padding(2),
	TimeSecAdapter(ULInt32("duration")),
	Flag("cheats"),
	Flag("complete"),
	Padding(14),
	Byte("map_size"),
	Byte("map_id"),
	Byte("population"),
	Padding(1),
	VictoryEnum(Byte("victory_type")),
	StartingAgeEnum(Byte("starting_age")),
	ResourceLevelEnum(Byte("resource_level")),
	Flag("all_techs"),
	Flag("team_together", truth = 0, falsehood = 1),
	RevealMapEnum(Byte("reveal_map")),
	Padding(3),
	Flag("lock_teams"),
	Flag("lock_speed"),
	Padding(1),
	Array(lambda ctx: ctx.player_num, achievements),
	Byte("index"),
	Padding(3),
    Padding(1512),
)