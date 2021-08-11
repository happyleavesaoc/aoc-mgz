"""Actions."""

from construct import (Array, Byte, Const, CString, Flag, Float32l, If,
                       Int16ul, Int32sl, Int32ul, Padding, Peek, String,
                       Struct, this, Bytes, Embedded, IfThenElse)

from mgz.body.achievements import achievements
from mgz.enums import (DiplomacyStanceEnum, FormationEnum, GameActionModeEnum,
                       OrderTypeEnum, ReleaseTypeEnum, ResourceEnum,
                       ResourceLevelEnum, RevealMapEnum, StanceEnum,
                       AgeEnum, VictoryEnum)
from mgz.util import TimeSecAdapter, check_flags

# pylint: disable=invalid-name, bad-continuation

# Not all actions are defined, not all actions are complete.


interact = "interact"/Struct(
    "player_id"/Byte,
    Const(b"\x00\x00"),
    "target_id"/Int32ul,
    "selected"/Int32ul,
    "x"/Float32l,
    "y"/Float32l,
    "next"/Peek(Bytes(8)),
    "flags"/If(lambda ctx: check_flags(ctx.next), Bytes(8)),
    "unit_ids"/If(lambda ctx: ctx.selected < 0xff, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

give_attribute = "give_attribute"/Struct(
    "player_id"/Byte,
    "target_id"/Byte,
    "attribute"/Byte,
    "amount"/Float32l
)

add_attribute = "add_attribute"/Struct(
    "player_id"/Byte,
    "attribute"/Byte,
    Padding(1),
    "amount"/Float32l
)

create = "create"/Struct(
    Padding(1),
    "unit_type"/Int16ul,
    "player_id"/Byte,
    Padding(1),
    "x"/Float32l,
    "y"/Float32l,
    "z"/Float32l
)

ai_interact = "ai_interact"/Struct(
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
    If(lambda ctx: ctx.selected < 0xff, Struct(
        "next"/Peek(Bytes(8)),
        "flags"/If(lambda ctx: check_flags(ctx.next), Bytes(8))
    )),
    "unit_ids"/If(lambda ctx: ctx.selected < 0xff, Array(
        lambda ctx: ctx.selected, Int32ul
    ))
)

ai_move = "ai_move"/Struct(
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
    Padding(4),
    Padding(4),
    Padding(4),
    If(lambda ctx: ctx.selected > 0x01, Array(
        lambda ctx: ctx.selected, "unit_ids"/Int32ul
    ))
)

resign = "resign"/Struct(
    "player_id"/Byte,
    "player_num"/Byte,
    "disconnected"/Flag
)

spec = "spec"/Struct(
    Padding(lambda ctx: ctx._._.length - 1)
)

queue = "queue"/Struct(
    Padding(3),
    "building_id"/Int32ul,
    "unit_type"/Int16ul,
    "number"/Int16ul,
)

multiqueue = "multiqueue"/Struct(
    Padding(3),
    "unit_type"/Int16ul,
    "num_buildings"/Byte,
    "queue_amount"/Byte,
    Array(lambda ctx: ctx.num_buildings, "building_ids"/Int32ul)
)

ai_queue = "ai_queue"/Struct(
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
    "next"/Peek(
        Struct(
            Padding(6),
            "check"/Int32sl
        )
    ),
    IfThenElse(lambda ctx: ctx.next.check == -1,
        Embedded(Struct(
            "selected"/Int16ul,
            "technology_type"/Int32ul,
            Array(lambda ctx: ctx.selected, "selected_ids"/Int32sl)
        )),
        Embedded(Struct(
            "technology_type"/Int16ul,
            Array(1, "selected_ids"/Int32sl)
        ))
    )
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
    StanceEnum("stance_type"/Byte),
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
    FormationEnum("formation_type"/Int32ul),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

save = "save"/Struct(
    "exited"/Flag,
    "player_id"/Byte,
    "filename"/CString(encoding='latin1'),
    Padding(lambda ctx: ctx._._.length - 23),
    "checksum"/Int32ul
)

chapter = "chapter"/Struct(
    "player_id"/Byte
)

build = "build"/Struct(
    "selected"/Byte,
    "player_id"/Int16ul,
    "x"/Float32l,
    "y"/Float32l,
    "building_type"/Int32ul,
    Padding(4),
    "sprite_id"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

game = "game"/Struct(
    "mode"/GameActionModeEnum("mode_id"/Byte),
    "player_id"/Byte,
    Padding(1),
    "diplomacy"/If(this.mode == 'diplomacy', Struct(
        "target_player_id"/Byte,
        Padding(3),
        "stance_float"/Float32l,
        "stance"/DiplomacyStanceEnum("stance_id"/Byte),
    )),
    "speed"/If(this.mode == 'speed', Struct(
        Padding(4),
        "speed"/Float32l,
        Padding(1)
    )),
    "instant_build"/If(this.mode == 'instant_build', Struct(
        Padding(9)
    )),
    "quick_build"/If(this.mode == 'quick_build', Struct(
        "status"/Flag,
        Padding(8),
    )),
    "allied_victory"/If(this.mode == 'allied_victory', Struct(
        "player_id"/Byte,
        "status"/Flag,
        Padding(7)
    )),
    "cheat"/If(this.mode == 'cheat', Struct(
        "cheat_id"/Byte,
        Padding(8)
    )),
    "unk0"/If(this.mode == 'unk0', Struct(
        Padding(9)
    )),
    "spy"/If(this.mode == 'spy', Struct(
        Padding(9)
    )),
    "unk1"/If(this.mode == 'unk1', Struct(
        Padding(9)
    )),
    "farm_queue"/If(this.mode == 'farm_queue', Struct(
        "amount"/Byte, # this seems to be a bit inconsistent between versions, needs more research
        Padding(8)
    )),
    "farm_unqueue"/If(this.mode == 'farm_unqueue', Struct(
        "amount"/Byte, # this seems to be a bit inconsistent between versions, needs more research
        Padding(8)
    )),
    # toggle farm auto seed queue
    "farm_autoqueue"/If(this.mode == 'farm_autoqueue', Struct(
        Padding(9)
    )),

    "fishtrap_queue" / If(this.mode == 'fishtrap_queue', Struct(
        "amount" / Byte,
        Padding(8)
    )),
    "fishtrap_unqueue" / If(this.mode == 'fishtrap_unqueue', Struct(
        "amount" / Byte,
        Padding(8)
    )),

    # toggle fish trap auto place queue
    "fishtrap_autoqueue"/If(this.mode == 'fishtrap_autoqueue', Struct(
        Padding(9)
    )),

    # toggles the default stance when units are created. All players start on aggressive by default, if the player
    # (initially) has defensive enabled it is called right before the first unit is queued, and again every time
    # the player toggles it in the game options menu
    "default_stance" / If(this.mode == 'default_stance', Struct(
        Padding(9)
    )),
    Padding(3)
)

droprelic = "droprelic"/Struct(
    Const(b"\x00\x00\x00"),
    'unit_id'/Int32ul
)

wall = "wall"/Struct(
    "selected"/Byte,
    "player_id"/Byte,
    IfThenElse(lambda ctx: ctx._._.length - 16 - (ctx.selected * 4) == 8,
        Embedded(Struct(
            Padding(1),
            "start_x"/Int16ul,
            "start_y"/Int16ul,
            "end_x"/Int16ul,
            "end_y"/Int16ul,
            "building_id"/Int32ul,
            Padding(4),
            "flags"/Bytes(4)
        )),
        Embedded(Struct(
            "start_x"/Byte,
            "start_y"/Byte,
            "end_x"/Byte,
            "end_y"/Byte,
            Padding(1),
            "building_id"/Int32ul,
            Padding(4),
        ))
    ),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
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
    "next"/Peek(Bytes(4)),
    "flags"/If(lambda ctx: check_flags(ctx.next), Bytes(4)),
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
    "next"/Peek(Bytes(4)),
    "flags"/If(lambda ctx: check_flags(ctx.next), Bytes(4)),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)


release = "release"/Struct(
    "selected"/Int16ul,
    Padding(1),
    "x"/Float32l, # -1 if none
    "y"/Float32l, # -1 if none
    ReleaseTypeEnum("release_type"/Byte),
    Padding(3),
    "release_id"/Int32ul,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)

"""
unload = "unload"/Struct(
    "selected"/Int16ul,
    Padding(1),
    "x"/Float32l, # -1 if none
    "y"/Float32l, # -1 if none
    Padding(4),
    Padding(4), # 0xffffffff
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)
"""

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

order = "order"/Struct(
    "selected"/Byte,
    Padding(2),
    "building_id"/Int32sl, # -1 cancels production queue
    OrderTypeEnum("order_type"/Byte),
    "cancel_order"/Byte, # when cancelling production queue, this indicates which item in the queue is to be cancelled
    Padding(2),
    "x"/Float32l,
    "y"/Float32l,
    Padding(4), # const
    "next"/Peek(Bytes(4)),
    "flags"/If(lambda ctx: check_flags(ctx.next), Bytes(4)),
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

ai_waypoint = "ai_waypoint"/Struct(
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

ai_command = "ai_command"/Struct(
    Padding(lambda ctx: ctx._._.length - 1)
)

"""DE Queue

In DE queue and multi queue share the same command
"""
de_queue = "de_queue"/Struct(
    "player_id"/Byte,
    "building_type"/Int16ul,
    "selected"/Byte,
    Padding(1),
    "unit_type"/Int16ul,
    "queue_amount"/Byte,
    Padding(1),
    Array(lambda ctx: ctx.selected, "building_ids"/Int32ul)
)

"""DE Attack Move

It's almost the same as Patrol.

10 X-coordinates followed by 10 Y-coordinates
First of each is popped off for consistency with other actions
"""
de_attackmove = "de_attackmove"/Struct(
    "selected"/Byte,
    "waypoints"/Int16ul,
    "x"/Float32l,
    Array(9, "x_more"/Float32l),
    "y"/Float32l,
    Array(9, "y_more"/Float32l),
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul),
)

postgame = "achievements"/Struct(
    Padding(3),
    "scenario_filename"/String(32, padchar=b'\x00', trimdir='right', encoding='latin1'),
    "player_num"/Byte,
    "computer_num"/Byte,
    Padding(2),
    Peek("duration_int"/Int32ul),
    TimeSecAdapter("duration"/Int32ul),
    "cheats"/Flag,
    "complete"/Flag,
    Padding(2),
    "db_checksum"/Int32ul,
    "code_checksum"/Int32ul,
    "version"/Float32l,
    "map_size"/Byte,
    "map_id"/Byte,
    "population"/Int16ul,
    Peek("victory_type_id"/Byte),
    VictoryEnum("victory_type"/Byte),
    Peek("starting_age_id"/Byte),
    AgeEnum("starting_age"/Byte),
    Peek("starting_resources_id"/Byte),
    ResourceLevelEnum("starting_resources"/Byte),
    "all_techs"/Flag,
    "random_positions"/Flag,
    RevealMapEnum("reveal_map"/Byte),
    "is_deathmatch"/Flag,
    "is_regicide"/Flag,
    "starting_units"/Byte,
    "lock_teams"/Flag,
    "lock_speed"/Flag,
    Padding(1),
    Array(lambda ctx: ctx.player_num, achievements),
    Padding(4),
    Array(lambda ctx: (8 - ctx.player_num) * 63, Padding(4)),
)

de_autoscout = "de_autoscout"/Struct(
    "selected"/Byte,
    Array(lambda ctx: ctx.selected, "unit_ids"/Int32ul)
)
