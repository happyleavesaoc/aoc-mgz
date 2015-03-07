from construct import *

"""Represents a single map type, defined by terrain type and elevation"""
tile = Struct("tile", 
	Byte("terrain_type"),
	Padding(1), # elevation
)

"""Map size and terrain"""
map_info = Struct("map_info",
	ULInt32("size_x"),
	ULInt32("size_y"),
	Value("tile_num", lambda ctx: ctx.size_x * ctx.size_y),
	ULInt32("next_struct_count"),
	Array(lambda ctx: ctx.next_struct_count,
		Struct("unk_restore_map",
			Padding(255), # 0xff
			Padding(lambda ctx: ctx._.tile_num), # 0x00
			Padding(1020), # 0x00
			Padding(172),
		)
	),
	Padding(2),
	Array(lambda ctx: ctx.tile_num, tile),
	ULInt32("num_data"),
	Padding(4),
	Array(lambda ctx: ctx.num_data, Padding(4)),
	Array(lambda ctx: ctx.num_data,
		Struct("couple",
			ULInt32("num"),
			Array(lambda ctx: ctx.num, Padding(8)),
		),
	),
	ULInt32("size_x_2"),
	ULInt32("size_y_2"),
	Padding(lambda ctx: ctx.tile_num * 4),
)