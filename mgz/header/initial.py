"""Initial."""

# pylint: disable=invalid-name,no-name-in-module

from construct import (Array, Byte, Embedded, Flag, Float32l, If, Int16ul, Int32sl,
                       Int32ul, Padding, String, Struct, Tell, this, Bytes)

from mgz.enums import MyDiplomacyEnum, TheirDiplomacyEnum
from mgz.header.objects import existing_object
from mgz.header.playerstats import player_stats
from mgz.util import Find, GotoObjectsEnd, RepeatUpTo

# Player attributes.
attributes = "attributes"/Struct(
    Array(lambda ctx: ctx._._._.replay.num_players, TheirDiplomacyEnum("their_diplomacy"/Byte)),
    Array(9, MyDiplomacyEnum("my_diplomacy"/Int32sl)),
    "allied_los"/Int32ul,
    "allied_victory"/Flag,
    "player_name_length"/Int16ul,
    "player_name"/Bytes(this.player_name_length - 1),
    Padding(1), # 0x00
    Padding(1), # 0x16
    "num_header_data"/Int32ul, # always 198
    Padding(1), # 0x21
    player_stats,
    Padding(1),
    "camera_x"/Float32l,
    "camera_y"/Float32l,
    "end_of_camera"/Tell,
    "num_saved_views"/Int32sl,
    # present in resumed games
    If(lambda ctx: ctx.num_saved_views > 0, Array(
        lambda ctx: ctx.num_saved_views, "saved_view"/Struct(
            "camera_x"/Float32l,
            "camera_y"/Float32l
        )
    )),
    "map_size"/Struct(
        "x"/Int16ul,
        "y"/Int16ul
    ),
    "culture"/Byte,
    "civilization"/Byte,
    "game_status"/Byte,
    "resigned"/Flag,
    Padding(1),
    "player_color"/Byte,
    Padding(1)
)


# Initial state of players, including Gaia.
player = "players"/Struct(
    attributes,
    "start_of_objects"/Find(b'\x0b\x00\x08\x00\x00\x00\x02\x00\x00', None),
    # If this isn't a restored game, we can read all the existing objects
    Embedded("not_restored"/If(this._.restore_time == 0, Struct(
        RepeatUpTo(b'\x00', existing_object),
        Padding(14),
        "end_of_objects"/GotoObjectsEnd() # Find the objects end just in case
    ))),

    # Can't parse existing objects in a restored game, skip the whole structure
    Embedded("is_restored"/If(this._.restore_time > 0, Struct(
        "end_of_objects"/GotoObjectsEnd(),
        # Just an empty array for now
        Array(0, existing_object)
    )))
)

# Initial state.
initial = "initial"/Struct(
    "restore_time"/Int32ul, # zero for non-restored
    "start_of_players"/Find(b'\x98\x9E\x00\x00\x02\x0B', None),
    Array(lambda ctx: ctx._.replay.num_players, player),
    Padding(19),
)
