"""Scenario."""

import struct
from construct import (Array, Float32l, Int16ul, Int32sl, Int32ul, Padding,
                       PascalString, Peek, String, Struct, Bytes, If, IfThenElse)

from mgz.enums import DifficultyEnum, PlayerTypeEnum, AgeEnum
from mgz.util import Find, Version, find_save_version, find_version
from mgz.header.de import de_string

# pylint: disable=invalid-name, bad-continuation

# Scenario header.
scenario_header = "scenario_header"/Struct(
    "next_uid"/Int32ul,
    "scenario_version"/Float32l,
    If(lambda ctx: find_save_version(ctx) >= 61.5, Struct(
        "player_capacity"/Int32ul,
        "gaia_player_index"/Int32ul
    )),
    Array(16, "tribe_names"/String(256)),
    Array(16, "player_names"/Int32ul),
    If(lambda ctx: find_save_version(ctx) >= 66.6, Array(16, "player_data"/Struct(
        "zeros"/Int32ul,
        "active"/Int32ul,
        "string_1"/de_string,
        "string_2"/de_string,
        "unknown"/Int32ul
    ))),
    If(lambda ctx: find_save_version(ctx) >= 61.5 and find_save_version(ctx) < 66.6, Bytes(64)),
    If(lambda ctx: find_save_version(ctx) < 66.6, Array(16, "player_data"/Struct(
        "active"/Int32ul,
        "human"/Int32ul,
        "civilization"/Int32ul,
        "civ_repeat"/If(lambda ctx: find_save_version(ctx) >= 13.34, Int32ul),
        "constant"/Int32ul, # 0x04 0x00 0x00 0x00
    ))),
    Padding(5),
    "elapsed_time"/Float32l,
    "scenario_filename"/PascalString(lengthfield="scenario_filename_length"/Int16ul),
    If(lambda ctx: ctx._._.version == Version.DE, Struct(
        Padding(64),
    )),
    If(lambda ctx: find_save_version(ctx) >= 66.6, Bytes(64)),
)

# Scenarios have intro text, a bitmap, and cinematics.
messages = "messages"/Struct(
    "instruction_id"/Int32sl,
    "hints_id"/Int32sl,
    "victory_id"/Int32sl,
    "defeat_id"/Int32sl,
    "history_id"/Int32sl,
    "scouts_id"/If(lambda ctx: ctx._._.version != Version.AOK, Int32sl),
    "instructions_length"/Int16ul,
    "instructions"/Bytes(lambda ctx: ctx.instructions_length),
    "hints"/PascalString(lengthfield="hints_length"/Int16ul),
    "victory"/PascalString(lengthfield="victory_length"/Int16ul),
    "defeat"/PascalString(lengthfield="defeat_length"/Int16ul),
    "history"/PascalString(lengthfield="history_length"/Int16ul),
    "scouts"/If(lambda ctx: ctx._._.version != Version.AOK, PascalString(lengthfield="scouts_length"/Int16ul)),
    "pg_cin"/PascalString(lengthfield="pg_cin_length"/Int16ul),
    "vict_cin"/PascalString(lengthfield="vict_cin_length"/Int16ul),
    "loss_cin"/PascalString(lengthfield="loss_cin_length"/Int16ul),
    "background"/PascalString(lengthfield="background_length"/Int16ul),
    "bitmap_included"/Int32ul,
    "bitmap_x"/Int32ul,
    "bitmap_y"/Int32ul,
    Padding(2),
    # bitmap here if it is included
    Padding(64), # 16 nulls
)

# Scenario player definitions.
scenario_players = "players"/Struct(
    Array(16, "ai_names"/PascalString(lengthfield="ai_name_length"/Int16ul)),
    Array(16, "ai"/Struct(Padding(8), "file"/PascalString(lengthfield="ai_file_length"/Int32ul))),
    Padding(4),
    Array(16, "resources"/Struct(
        "gold"/Int32ul,
        "wood"/Int32ul,
        "food"/Int32ul,
        "stone"/Int32ul,
        "unk0"/Int32ul,
        "unk1"/Int32ul,
        If(lambda ctx: ctx._._._.version in (Version.DE, Version.HD),
            "unk2"/Int32ul
        )
    )),
    Array(16, Padding(1)) # 0x01 x 16
)

# Victory conditions.
victory = "victory"/Struct(
    Padding(4),
    "is_conquest"/Int32ul,
    Padding(4),
    "relics"/Int32ul,
    Padding(4),
    "explored"/Int32ul,
    Padding(4),
    "all"/Int32ul,
    "mode"/Int32ul,
    "score"/Int32ul,
    "time"/Int32ul,
)

# Disabled techs, units, and buildings.
disables = "disables"/Struct(
    Padding(4),
    Padding(64),
    If(lambda ctx: ctx._._.version != Version.DE,
        Struct(
            Array(16, "num_disabled_techs"/Int32ul),
            Array(16, Array(30, Padding(4))),
            Array(16, "num_disabled_units"/Int32ul),
            Array(16, Array(30, Padding(4))),
            Array(16, "num_disabled_buildings"/Int32ul),
            Array(16, Array(20, Padding(4))),
        )
    ),
    If(lambda ctx: ctx._._.version == Version.DE, Bytes(196)),
    If(lambda ctx: ctx._._.version == Version.HD, Bytes(644)),
    "padding"/Bytes(12)
)

# Game settings.
game_settings = "game_settings"/Struct(
    Array(16, AgeEnum("starting_ages"/Int32sl)),
    "hd"/If(lambda ctx: find_version(ctx) == Version.HD, Bytes(16)),
    Padding(4),
    Padding(8),
    "map_id"/If(lambda ctx: ctx._._.version != Version.AOK, Int32ul),
    Peek("difficulty_id"/Int32ul),
    DifficultyEnum("difficulty"/Int32ul),
    "lock_teams"/Int32ul,
    If(lambda ctx: ctx._._.version == Version.DE,
        Struct(
            Padding(29),
            If(lambda ctx: find_save_version(ctx) >= 13.07, Padding(1)),
            If(lambda ctx: find_save_version(ctx) >= 13.34, Padding(132)),
            If(lambda ctx: find_save_version(ctx) >= 20.06, Padding(1)),
            If(lambda ctx: find_save_version(ctx) >= 20.16, Padding(4)),
            If(lambda ctx: find_save_version(ctx) >= 25.02, Padding(4*16)),
            If(lambda ctx: 26.21 > find_save_version(ctx) >= 25.06, Padding(4))
        )
    ),
    Array(9, "player_info"/Struct(
        "slot"/Int32sl,
        PlayerTypeEnum("type"/Int32ul),
        "name"/PascalString(lengthfield="name_length"/Int32ul)
    )),
    Padding(36),
    Padding(4),
    IfThenElse(lambda ctx: ctx._._.version == Version.DE,
        Struct(
            If(lambda ctx: find_save_version(ctx) < 13.34, Find(struct.pack('<d', 2.2), None)),
            If(lambda ctx: 25.06 > find_save_version(ctx) >= 13.34, Find(struct.pack('<d', 2.4), None)),
            If(lambda ctx: 25.22 > find_save_version(ctx) >= 25.06, Find(struct.pack('<d', 2.5), None)),
            If(lambda ctx: 26.16 > find_save_version(ctx) >= 25.22, Find(struct.pack('<d', 2.6), None)),
            If(lambda ctx: 26.21 > find_save_version(ctx) >= 26.16, Find(struct.pack('<d', 3.0), None)),
            If(lambda ctx: 37 > find_save_version(ctx) >= 26.21, Find(struct.pack('<d', 3.2), None)),
            If(lambda ctx: 61.5 > find_save_version(ctx) >= 37, Find(struct.pack('<d', 3.5), None)),
            If(lambda ctx: 63 > find_save_version(ctx) >= 61.5, Find(struct.pack('<d', 3.6), None)),
            If(lambda ctx: 64.3 > find_save_version(ctx) >= 63, Find(struct.pack('<d', 3.9), None)),
            If(lambda ctx: 66.3 > find_save_version(ctx) >= 64.3, Find(struct.pack('<d', 4.1), None)),
            If(lambda ctx: find_save_version(ctx) >= 66.3, Find(struct.pack('<d', 4.5), None)),
        ),
        "end_of_game_settings"/Find(b'\x9a\x99\x99\x99\x99\x99\xf9\\x3f', None),
    ),
)


# Triggers.
triggers = "triggers"/Struct(
    Padding(1),
    "num_triggers"/Int32ul,
    # parse if num > 0
    "de"/If(lambda ctx: ctx._._.version == Version.DE,
         Padding(1032)
    )
)



# Scenario metadata.
scenario = "scenario"/Struct(
    scenario_header,
    messages,
    scenario_players,
    victory,
    Padding(12544), # unknown
    disables,
    game_settings,
    triggers
)
