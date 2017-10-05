"""Map info."""

from construct import (Array, Byte, Computed, Embedded, If, Int32ul, Padding,
                       Struct)

# pylint: disable=invalid-name


# Represents a single map type, defined by terrain type and elevation.
tile = "tile"/Struct(
    "terrain_type"/Byte,
    # UP 1.5 terrain structure
    Embedded("up15"/If(lambda ctx: ctx.terrain_type == 255, Struct(
        "terrain_type_up"/Byte,
        Padding(1)
    ))),
    Padding(1), # elevation
)

# Map size and terrain.
map_info = "map_info"/Struct(
    "size_x"/Int32ul,
    "size_y"/Int32ul,
    "tile_num"/Computed(lambda ctx: ctx.size_x * ctx.size_y),
    "next_struct_count"/Int32ul,
    Array(lambda ctx: ctx.next_struct_count, "unk_restore_map"/Struct(
        Padding(255), # 0xff
        Padding(lambda ctx: ctx._.tile_num), # 0x00
        Padding(1020), # 0x00
        Padding(172)
    )),
    Padding(2),
    Array(lambda ctx: ctx.tile_num, tile),
    "num_data"/Int32ul,
    Padding(4),
    Array(lambda ctx: ctx.num_data, Padding(4)),
    Array(lambda ctx: ctx.num_data, "couple"/Struct(
        "num"/Int32ul,
        Array(lambda ctx: ctx.num, Padding(8))
    )),
    "size_x_2"/Int32ul,
    "size_y_2"/Int32ul,
    Padding(lambda ctx: ctx.tile_num * 4),
)
