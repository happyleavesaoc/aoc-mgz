"""Definitive Edition structure."""

from construct import (
    Struct, Int32ul, Float32l, Array, Padding, Flag,
    Byte, Int16ul, Bytes, Int32sl, Peek, Const, RepeatUntil
)

from mgz.enums import VictoryEnum, ResourceLevelEnum, AgeEnum, PlayerTypeEnum, DifficultyEnum

# pylint: disable=invalid-name, bad-continuation

de_string = Struct(
    Const(b"\x60\x0A"),
    "length"/Int16ul,
    "value"/Bytes(lambda ctx: ctx.length)
)

separator = Const(b"\xa3_\x02\x00")

de = "de"/Struct(
    "options"/Int32sl,
    Int32ul,
    Int32ul,
    "dlc_count"/Int32ul,
    "dlc_ids"/Array(lambda ctx: ctx.dlc_count, Int32ul),
    Bytes(4),
    "difficulty"/DifficultyEnum(Int32ul),
    "map_size"/Int32ul,
    "map_id"/Int32ul,
    "reveal_map"/Int32ul,
    Peek("victory_type_id"/Int32ul),
    VictoryEnum("victory_type"/Int32ul),
    Peek("starting_resources_id"/Int32ul),
    ResourceLevelEnum("starting_resources"/Int32ul),
    Peek("starting_age_id"/Int32ul),
    AgeEnum("starting_age"/Int32ul),
    Peek("ending_age_id"/Int32ul),
    AgeEnum("ending_age"/Int32ul),
    "game_type"/Int32ul,
    separator,
    separator,
    "speed"/Float32l,
    "treaty_length"/Int32ul,
    "population_limit"/Int32ul,
    "num_players"/Int32ul,
    Int32ul,
    Int32ul,
    separator,
    "trade_enabled"/Flag,
    "team_bonus_disabled"/Flag,
    "random_positions"/Flag,
    "all_techs"/Flag,
    "num_starting_units"/Byte,
    "lock_teams"/Flag,
    "lock_speed"/Flag,
    "multiplayer"/Flag,
    "cheats"/Flag,
    "record_game"/Flag,
    "animals_enabled"/Flag,
    "predators_enabled"/Flag,
    Bytes(3),
    separator,
    "players"/Array(8, Struct(
        "dlc_id"/Int32ul,
        "color_id"/Int32sl,
        "selected_color"/Byte,
        Byte,
        "team_id"/Byte,
        Bytes(9),
        "civ_id"/Byte,
        Const(b"\x00\x00\x00"),
        "ai_type"/de_string,
        Byte,
        "ai_name"/de_string,
        "name"/de_string,
        "type"/PlayerTypeEnum(Int32ul),
        "profile_id"/Int32ul,
        Const(b"\x00\x00\x00\x00"),
        "player_number"/Int32sl,
        Bytes(10),
    )),
    "fog_of_war"/Flag,
    "cheat_notifications"/Flag,
    "colored_chat"/Flag,
    Bytes(4),
    "ranked"/Flag,
    "allow_specs"/Flag,
    Bytes(3),
    separator,
    Bytes(12),
    "strings"/Array(23,
        Struct(
            "string"/de_string,
            RepeatUntil(lambda x, lst, ctx: lst[-1] not in [3, 21, 42], Int32ul)
        )
    ),
    "strategic_numbers"/Array(59, Int32sl),
    "num_ai_files"/Int32ul,
    Const(b"\x00\x00\x00\x00"),
    "ai_files"/Array(lambda ctx: ctx.num_ai_files, Struct(
        Bytes(4),
        "name"/de_string,
        Bytes(4),
    )),
    "guid"/Bytes(16),
    "lobby_name"/de_string,
    de_string,
    Bytes(19),
    de_string,
    Bytes(5),
    de_string,
    Int32ul,
    Bytes(4) # usually zero
)
