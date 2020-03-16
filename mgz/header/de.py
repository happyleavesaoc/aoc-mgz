"""Definitive Edition structure."""

from construct import (
    Struct, Int32ul, Float32l, Array, Padding, Flag,
    Byte, Int16ul, Bytes, Int32sl, Peek, Const, RepeatUntil
)

from mgz.enums import VictoryEnum, ResourceLevelEnum, AgeEnum

# pylint: disable=invalid-name, bad-continuation

de = "de"/Struct(
    "options"/Int32sl,
    "unk0"/Int32ul,
    "unk1"/Int32ul,
    "dlc_count"/Int32ul,
    "dlc_ids"/Array(lambda ctx: ctx.dlc_count, Int32ul),
    Padding(4),
    "difficulty"/Int32ul,
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
    Padding(8),
    "speed"/Float32l,
    "treaty_length"/Int32ul,
    "population_limit"/Int32ul,
    "num_players"/Int32ul,
    "unknown2"/Int32ul,
    "unknown3"/Int32ul,
    Padding(4),
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
    Padding(6),
    "players"/Array(8, Struct(
        "dat_crc"/Bytes(4),
        "mp_version"/Byte,
        "color_id"/Int32sl,
        Bytes(12),
        "civ_id"/Byte,
        Bytes(14),
        "name_length"/Int16ul,
        "name"/Bytes(lambda ctx: ctx.name_length),
        Padding(4),
        "profile_id"/Int32ul,
        Bytes(17)
    )),
    Padding(1),
    "fog_of_war"/Flag,
    "cheat_notifications"/Flag,
    "colored_chat"/Flag,
    Padding(4),
    "ranked"/Flag,
    "allow_specs"/Flag,
    Padding(19),
    "strings"/Array(23,
        Struct(
            Const(b"\x60\x0A"),
            "len"/Int16ul,
            "string"/Bytes(lambda ctx: ctx.len),
            RepeatUntil(lambda x, lst, ctx: lst[-1] not in [3, 21, 42], Int32ul)
        )
    ),
    Padding(244),
    "guid"/Bytes(16),
    Padding(2),
    "lobby_name_length"/Int16ul,
    "lobby_name"/Bytes(lambda ctx: ctx.lobby_name_length),
    Padding(44)
)
