"""Map info."""

from construct import (Array, Byte, Computed, Embedded, Flag, IfThenElse,
                       Int32ul, Padding, Struct, Int16sl)

# pylint: disable=invalid-name, bad-continuation


# Represents a single map type, defined by terrain type and elevation.
tile = "tile"/Struct(
    "terrain_type"/Byte,
    Embedded(IfThenElse(lambda ctx: ctx._._.version == 'VER 9.4',
        Embedded(Struct(
            "terrain_type"/Byte,
            "elevation"/Byte,
            "unk0"/Int16sl,
            "unk1"/Int16sl,
            "unk2"/Int16sl
        )),
        Embedded(IfThenElse(lambda ctx: ctx.terrain_type == 255, Struct(
            "terrain_type"/Byte,
            "elevation"/Byte,
            Padding(1)
        ), Struct(
            "elevation"/Byte
        )))
    ))
)


# Map size and terrain.
map_info = "map_info"/Struct(
    "size_x"/Int32ul,
    "size_y"/Int32ul,
    "tile_num"/Computed(lambda ctx: ctx.size_x * ctx.size_y),
    "zone_num"/Int32ul,
    Array(lambda ctx: ctx.zone_num, Struct(
        IfThenElse(lambda ctx: ctx._._.version == 'VER 9.4',
            Padding(lambda ctx: 2048 + (ctx._.tile_num * 2)),
            Padding(lambda ctx: 1275 + ctx._.tile_num)
        ),
        "num_floats"/Int32ul,
        Padding(lambda ctx: ctx.num_floats * 4),
        Padding(4)
    )),
    "all_visible"/Flag,
    "fog_of_war"/Flag,
    Array(lambda ctx: ctx.tile_num, tile),
    "num_data"/Int32ul,
    Padding(4),
    Array(lambda ctx: ctx.num_data, Padding(4)),
    Array(lambda ctx: ctx.num_data, "couple"/Struct(
        "num_obstructions"/Int32ul,
        Array(lambda ctx: ctx.num_obstructions, Padding(8))
    )),
    "size_x_2"/Int32ul,
    "size_y_2"/Int32ul,
    Padding(lambda ctx: ctx.tile_num * 4), # visibility
)
