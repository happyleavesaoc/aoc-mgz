from construct import *
from mgz.header.objects import *
from mgz.header.playerstats import *
from mgz.enums import *
from mgz.util import *

"""Player attributes"""
attributes = Struct("attributes",
    Array(lambda ctx: ctx._._._.replay.num_players, TheirDiplomacyEnum(Byte("their_diplomacy"))),
    Array(9, MyDiplomacyEnum(SLInt32("my_diplomacy"))),
    Padding(5),
    ULInt16("player_name_length"),
    String("player_name", lambda ctx: ctx.player_name_length, padchar = '\x00', trimdir = 'right'),
    Padding(1), # 0x16
    ULInt32("num_header_data"), # always 198
    Padding(1), # 0x21
    player_stats,
    Padding(1),
    LFloat32("camera_x"),
    LFloat32("camera_y"),
    Anchor("end_of_camera"),
    SLInt32("num_unk"),
    If(lambda ctx: ctx.num_unk > 0, # present in resumed games
        Array(lambda ctx: ctx.num_unk, Struct("unk_structure", Padding(8))),
    ),
    Padding(5),
    Byte("civilization"),
    Padding(3),
    Byte("player_color"),
    Padding(1),
)

"""Initial state of players, including Gaia"""
player = Struct("players",
    attributes,
    Padding(4182),
    LFloat32("some_float"),
    ULInt32("num_researches"),
    Padding(2),
    Padding(lambda ctx: ctx.num_researches * 24),
    Find("end_of_unknown_bytes", b'\x62\x03', 50000),
    Padding(2),
    Array(866, ULInt32("defaults")),
    Const("\x0b\x16"),
    Array(lambda ctx: ctx.defaults.count(1), default_object),
    ULInt32("map_size_x"),
    ULInt32("map_size_y"),
    Padding(6),
    Padding(lambda ctx: ctx.map_size_x * ctx.map_size_y), # los
    Padding(4),
    Padding(4),
    ULInt32("num_unknowns"), # supposedly, but doesn't seem to match, so we have to use Find
    Padding(32),
    Find("start_of_objects", b'\x0b\x00\x08\x00\x00\x00\x02\x00\x00', None),
    # If this isn't a restored game, we can read all the existing objects
    If(lambda ctx: ctx._.restore_time == 0, Embed(Struct("non_restore",
            RepeatUpTo(b'\x00', existing_object),
            Padding(14),
        ))
    ),
    # Can't parse existing objects in a restored game, skip the whole structure
    If(lambda ctx: ctx._.restore_time > 0, Embed(Struct("restore",
            GotoObjectsEnd("end_of_objects"),
            # Just an empty array for now
            Array(0, existing_object)
        )),
    ),
)

"""Initial state"""
initial = Struct("initial",
    ULInt32("restore_time"), # zero for non-restored
    Find("start_of_players", b'\x98\x9E\x00\x00\x02\x0B', None),
    Array(lambda ctx: ctx._.replay.num_players, player),
    Padding(19),
)
