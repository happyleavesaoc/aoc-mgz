from construct import *
from aoc.mgz.enums import *
from aoc.mgz.util import *

"""Scenario Header"""
scenario_header = Struct("scenario_header",
	ULInt32("next_uid"),
	ULInt32("constant"),
	Array(16, String("names", 256)),
	Array(16, ULInt32("string_ids")),
	Array(16, Struct("player_data",
		ULInt32("active"),
		ULInt32("human"),
		ULInt32("civilization"),
		ULInt32("constant"), # 0x04 0x00 0x00 0x00
	)),
	Padding(5),
	LFloat32("elapsed_time"),
	PascalString("scenario_filename", length_field = ULInt16("scenario_filename_length")),
)

"""Scenarios have intro text, a bitmap, and cinematics"""
messages = Struct("messages",
	ULInt32("instruction_id"),
	ULInt32("hints_id"),
	ULInt32("victory_id"),
	ULInt32("defeat_id"),
	ULInt32("history_id"),
	ULInt32("scouts_id"),
	PascalString("instructions", length_field = ULInt16("instructions_length")), # this contains the map name
	PascalString("hints", length_field = ULInt16("hints_length")),
	PascalString("victory", length_field = ULInt16("victory_length")),
	PascalString("defeat", length_field = ULInt16("defeat_length")),
	PascalString("history", length_field = ULInt16("history_length")),
	PascalString("scouts", length_field = ULInt16("scouts_length")),
	PascalString("pg_cin", length_field = ULInt16("pg_cin_length")),
	PascalString("vict_cin", length_field = ULInt16("vict_cin_length")),
	PascalString("loss_cin", length_field = ULInt16("loss_cin_length")),
	PascalString("background", length_field = ULInt16("background_length")),
	ULInt32("bitmap_included"),
	ULInt32("bitmap_x"),
	ULInt32("bitmap_y"),
	Padding(2),
	# bitmap here if it is included
	Padding(64), # 16 nulls
)

"""Scenario player definitions"""
scenario_players = Struct("players",
	Array(16, PascalString("ai_names", length_field = ULInt16("ai_name_length"))),
	Array(16, Struct("ai", Padding(8), PascalString("file", length_field = ULInt32("ai_file_length")))),
	Padding(4),
	Array(16, Struct("resources",
		ULInt32("gold"),
		ULInt32("wood"),
		ULInt32("food"),
		ULInt32("stone"),
		Padding(8),
	)),
	Array(16, Padding(1)), # 0x01 x 16
)

"""Victory conditions"""
victory = Struct("victory",
	Padding(4),
	ULInt32("is_conquest"),
	Padding(4),
	ULInt32("relics"),
	Padding(4),
	ULInt32("explored"),
	Padding(4),
	ULInt32("all"),
	ULInt32("mode"),
	ULInt32("score"),
	ULInt32("time"),
)

"""Disabled techs, units, and buildings"""
disables = Struct("disables",
	Padding(4),
	Padding(64),
	Array(16, ULInt32("num_disabled_techs")),
	Array(16, Array(30, Padding(4))),
	Array(16, ULInt32("num_disabled_units")),
	Array(16, Array(30, Padding(4))),
	Array(16, ULInt32("num_disabled_buildings")),
	Array(16, Array(20, Padding(4))),
	Padding(12),
)

"""Game settings"""
game_settings = Struct("game_settings",
	Array(16, StartingAgeEnum(SLInt32("starting_ages"))),
	Padding(4),
	Padding(8),
	ULInt32("map_id"),
	DifficultyEnum(ULInt32("difficulty")),
	Padding(4),
	Array(9, Struct("player_info", ULInt32("data_ref"), PlayerTypeEnum(ULInt32("type")), PascalString("name",  length_field = ULInt32("name_length")))),
	Padding(36),
	Padding(4),
	Find("end_of_game_settings", b'\x9a\x99\x99\x99\x99\x99\xf9\x3f', None),
)

"""Triggers"""
triggers = Struct("triggers",
	Padding(1),
	ULInt32("num_triggers"),
	# parse if num > 0
)

"""Scenario metadata"""
scenario = Struct("scenario",
	scenario_header,
	messages,
	scenario_players,
	victory,
	Padding(12544), # unknown
	disables,
	game_settings,
	triggers,
)