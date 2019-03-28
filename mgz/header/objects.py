"""Objects."""

from construct import (Array, Byte, Embedded, Flag, Float32l, If, Int16sl, Int16ub,
                       Int16ul, Int32ub, Int32ul, Padding, Peek, Struct,
                       Switch)

from mgz.enums import ObjectEnum, ObjectTypeEnum, ResourceEnum
from mgz.util import Find

# pylint: disable=invalid-name


# Object IDs can be looked up via Advanced Genie Editor.

# Existing objects all have the same header.
existing_object_header = "header"/Struct(
    ObjectEnum("object_type"/Int16ul),
    "sprite"/Int16ul,
    "inside_id"/Int32ul,
    "hitpoints"/Float32l,
    "object_state"/Byte,
    "sleep"/Flag,
    "doppleganger"/Flag,
    "go_to_sleep"/Flag,
    "object_id"/Int32ul,
    "facet"/Byte,
    "x"/Float32l,
    "y"/Float32l,
    "z"/Float32l,
    "screen_offset_x"/Int16ul,
    "screen_offset_y"/Int16ul,
    "shadow_offset_x"/Int16ul,
    "shadow_offset_y"/Int16ul,
    ResourceEnum("resource_type"/Int16sl),
    "amount"/Float32l,
)

additional_header = "additional_header"/Struct(
    Embedded(existing_object_header),
    "worker_count"/Byte,
    "current_damage"/Byte,
    "damaged_lately_timer"/Byte,
    "under_attack"/Byte,
    "pathing_group_len"/Int32ul,
    "pathing_group"/Array(lambda ctx: ctx.pathing_group_len, Int32ul),
    "group_id"/Byte,
    "already_called"/Byte,
)

# Other - seems to be items under Units > Other in the scenario editor
other = "other"/Struct(
    Embedded(additional_header),
    # The following sections can be refined with further research.
    # There are clearly some patterns.
    "has_extra"/Byte,
    If(lambda ctx: ctx.has_extra == 2, Padding(
        34
    )),
    "speed"/Float32l
)

# Units - typically villagers, scout, and any sheep within LOS
unit = "unit"/Struct(
    Embedded(additional_header),
    # Not pretty, but we don't know how to parse a unit yet.
    # Also, this only works on non-restored games.
    # This isn't a constant footer, these are actually initial values of some sort.
    "end_of_unit"/Find(b'\xff\xff\xff\xff\x00\x00\x80\xbf\x00\x00\x80\xbf\xff\xff\xff' \
                       b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00', None)
)

# Buildings - ID doesn't match Build action ID - buildings can have multiple parts
building = "building"/Struct(
    Embedded(additional_header),
    # The following sections can be refined with further research.
    # There are clearly some patterns.
    "has_extra"/Byte,
    If(lambda ctx: ctx.has_extra == 2, Padding(
        17
    )),
    Padding(16),
    "has_extra2"/Byte,
    If(lambda ctx: ctx.has_extra2 == 1, Padding(
        17
    )),
    Padding(127),
    "c1"/Int16ul,
    "c2"/Int16ul,
    If(lambda ctx: ctx.c1 > 0, "more"/Struct(
        Array(lambda ctx: ctx._.c2, Padding(8)),
        Padding(2)
    )),
    Padding(274),
    "num"/Byte,
    If(lambda ctx: ctx.num < 100, Array(
        lambda ctx: ctx.num, "id2"/Int32ul
    )),
    Padding(93),
)

# Mainly trees and mines
gaia = "gaia"/Struct(
    Embedded(existing_object_header),
    Padding(14),
)

# This type has various classes of objects, we care about the fish
fish = "fish"/Struct(
    Embedded(additional_header),
    "has_extra"/Byte,
    If(lambda ctx: ctx.has_extra == 2, Padding(
        17
    )),
    Padding(140)
)

# Objects that exist on the map at the start of the recorded game
existing_object = "objects"/Struct(
    ObjectTypeEnum("type"/Byte),
    "player_id"/Byte,
    Embedded("properties"/Switch(lambda ctx: ctx.type, {
        "gaia": gaia,
        "unit": unit,
        "building": building,
        "fish": fish,
        "other": other,
        "doppelganger": other
    })),
    # These boundary bytes can occur in the middle of a set of objects, and at the end
    # There is probably a better way to check these
    Peek("extension1"/Int16ub),
    Peek("extension2"/Int32ub),
    If(lambda ctx: ctx.extension1 == 11 and ctx.extension2 > 720898, Padding(
        10
    ))
)

# Default values for objects, nothing of real interest
default_object = "default_object"/Struct(
    ObjectTypeEnum("type"/Byte),
    Padding(14),
    "properties"/Switch(lambda ctx: ctx.type, {
        "gaia": Padding(24),
        "object": Padding(32),
        "fish": Padding(32),
        "other": Padding(28),
    }, default="end_of_object"/Find(b'\x21\x16', 200))
)
