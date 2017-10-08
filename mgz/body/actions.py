"""Actions."""

from construct import (Array, Byte, Const, CString, Flag, Float32l, If,
                       Int16ul, Int32sl, Int32ul, Padding, String, Struct)

from mgz.body.achievements import achievements
from mgz.enums import (ResourceEnum, ResourceLevelEnum, RevealMapEnum,
                       StartingAgeEnum, VictoryEnum)
from mgz.util import TimeSecAdapter

# pylint: disable=invalid-name

# Not all actions are defined, not all actions are complete.

attack = "attack"/Struct(
    "player_id"/Byte,
    Const(b"\x00\x00"),
    "target_id"/Int32ul,
    "selected"/Int32ul,
    "x"/Float32l,
    "y"/Float32l,
    If(lambda ctx: ctx.selected < 0xff, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

aiattack = "aiattack"/Struct(
    Padding(3),
    "target_id"/Int32ul,
    "selected"/Byte,
    Padding(3),
    "x"/Float32l,
    "y"/Float32l,
    If(lambda ctx: ctx.selected < 0xff, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

move = "move"/Struct(
    "player_id"/Byte,
    Const(b"\x00\x00"),
    Padding(4),
    "selected"/Int32ul,
    "x"/Float32l,
    "y"/Float32l,
    If(lambda ctx: ctx.selected < 0xff, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

aimove = "aimove"/Struct(
    "selected"/Byte,
    "player_id"/Byte,
    "player_num"/Byte,
    Padding(4),
    Padding(4),
    "target_id"/Int32ul,
    Padding(1),
    Padding(3),
    "x"/Float32l,
    "y"/Float32l,
    If(lambda ctx: ctx.selected > 0x01, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

resign = "resign"/Struct(
    "player_id"/Byte,
    "player_num"/Byte,
    "disconnected"/Flag
)

train = "train"/Struct(
    Padding(3),
    "building_id"/Int32ul,
    "unit_type"/Int16ul,
    "number"/Int16ul,
)

aitrain = "aitrain"/Struct(
    Padding(3),
    "building_id"/Int32ul,
    "player_id"/Int16ul,
    "unit_type"/Int16ul,
    Padding(4)
)

research = "research"/Struct(
    Padding(3),
    "building_id"/Int32ul,
    "player_id"/Int16ul,
    "technology_type"/Int16ul,
    Padding(4),
)

sell = "sell"/Struct(
    "player_id"/Byte,
    ResourceEnum("resource_type"/Byte),
    "amount"/Byte,
    Padding(4)
)

buy = "buy"/Struct(
    "player_id"/Byte,
    ResourceEnum("resource_type"/Byte),
    "amount"/Byte,
    Padding(4)
)

stop = "stop"/Struct(
    "selected"/Byte,
    Array(lambda ctx: ctx.selected, "object_ids"/Int32ul)
)

stance = "stance"/Struct(
    "selected"/Byte,
    "stance_type"/Byte,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

guard = "guard"/Struct(
    "selected"/Byte,
    Padding(2),
    "guarded_unit_id"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

follow = "follow"/Struct(
    "selected"/Byte,
    Padding(2),
    "followed_unit_id"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

formation = "formation"/Struct(
    "selected"/Byte,
    "player_id"/Int16ul,
    "formation_type"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

multiplayersave = "multiplayersave"/Struct(
    "player_id"/Int16ul,
    Padding(5),
    "filename"/CString()
)

saveandexit = "saveandexit"/Struct(
    "exited"/Flag,
    "player_id"/Byte,
    Padding(253) # checksum?
)

build = "build"/Struct(
    "selected"/Byte,
    "player_id"/Int16ul,
    "x"/Float32l,
    "y"/Float32l,
    "building_type"/Int32ul,
    Padding(8),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

# Diplomacy, game speed, and cheats
gamespeed = "gamespeed"/Struct(
    "mode"/Byte,
    "player_id"/Byte,
    Padding(1),
    "option"/Byte,
    Padding(3),
    "unk"/Float32l,
    "diplomatic_stance"/Byte,
    Padding(3)
)

wall = "wall"/Struct(
    "selected"/Byte,
    "player_id"/Byte,
    Padding(4),
    Padding(1),
    "building_id"/Int32ul,
    Padding(4),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul),
)

delete = "delete"/Struct(
    Padding(3),
    "object_id"/Int32ul,
    "player_id"/Int32ul
)

attackground = "attackground"/Struct(
    "selected"/Byte,
    Padding(2),
    "x"/Float32l,
    "y"/Float32l,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

tribute = "tribute"/Struct(
    "player_id"/Byte,
    "player_id_to"/Byte,
    ResourceEnum("resource_type"/Byte),
    "amount"/Float32l,
    "fee"/Float32l
)

repair = "repair"/Struct(
    "selected"/Byte,
    Padding(2),
    "repaired_id"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

unload = "unload"/Struct(
    "selected"/Int16ul,
    Padding(1),
    "x"/Float32l, # -1 if none
    "y"/Float32l, # -1 if none
    Padding(4),
    Padding(4), # 0xffffffff
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

togglegate = "togglegate"/Struct(
    Padding(3),
    "gate_id"/Int32ul
)

flare = "flare"/Struct(
    Padding(7),
    Array(9, "player_ids"/Byte),
    Padding(3),
    "x"/Float32l,
    "y"/Float32l,
    "player_id"/Byte,
    "player_number"/Byte,
    Padding(2)
)

garrison = "garrison"/Struct(
    "selected"/Byte,
    Padding(2),
    "building_id"/Int32sl, # -1 cancels production queue
    "u0"/Int32ul,
    "x"/Float32l,
    "y"/Float32l,
    Padding(4), # const
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul),
)

gatherpoint = "gatherpoint"/Struct(
    "selected"/Byte,
    Padding(2),
    "target_id"/Int32ul,
    "target_type"/Int32ul,
    "x"/Float32l,
    "y"/Float32l,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

townbell = "townbell"/Struct(
    Padding(3),
    "towncenter_id"/Int32ul,
    "active"/Int32ul
)

"""Patrol

10 X-coordinates followed by 10 Y-coordinates
First of each is popped off for consistency with other actions
"""
patrol = "patrol"/Struct(
    "selected"/Byte,
    "waypoints"/Int16ul,
    "x"/Float32l,
    Array(9, "x_more"/Float32l),
    "y"/Float32l,
    Array(9, "y_more"/Float32l),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul),
)

waypoint = "waypoint"/Struct(
    Padding(1),
    "selected"/Byte,
    "x"/Byte,
    "y"/Byte,
    "building_ids"/If(lambda ctx: ctx.selected != 255, Array(
        lambda ctx: ctx.selected, Int32ul
    ))
)

aiwaypoint = "aiwaypoint"/Struct(
    "selected"/Byte,
    "waypoint_count"/Byte,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul),
    Array(lambda ctx: ctx.waypoint_count, "x_more"/Byte),
    Array(lambda ctx: ctx.waypoint_count, "y_more"/Byte)
)

backtowork = "backtowork"/Struct(
    Padding(3),
    "towncenter_id"/Int32ul
)

postgame = "achievements"/Struct(
    Padding(3),
    "scenario_filename"/String(32, padchar=b'\x00', trimdir='right'),
    "player_num"/Byte,
    "computer_num"/Byte,
    Padding(2),
    TimeSecAdapter("duration"/Int32ul),
    "cheats"/Flag,
    "complete"/Flag,
    Padding(14),
    "map_size"/Byte,
    "map_id"/Byte,
    "population"/Byte,
    Padding(1),
    VictoryEnum("victory_type"/Byte),
    StartingAgeEnum("starting_age"/Byte),
    ResourceLevelEnum("resource_level"/Byte),
    "all_techs"/Flag,
    "team_together"/Flag, #(truth = 0, falsehood = 1),
    RevealMapEnum("reveal_map"/Byte),
    "is_deathmatch"/Flag,
    "is_regicide"/Flag,
    Padding(1),
    "lock_teams"/Flag,
    "lock_speed"/Flag,
    Padding(1),
    Array(lambda ctx: ctx.player_num, achievements),
    Padding(4),
    Array(lambda ctx: (8 - (ctx.player_num + ctx.computer_num)) * 63, Padding(4)),
)
