"""Definitive Edition structure."""

from construct import (
    Struct, Int32ul, Float32l, Array, Padding, Flag, If,
    Byte, Int16ul, Bytes, Int32sl, Peek, Const, RepeatUntil,
    Int64ul, Computed
)

from mgz.enums import VictoryEnum, ResourceLevelEnum, AgeEnum, PlayerTypeEnum, DifficultyEnum
from mgz.util import find_save_version

# pylint: disable=invalid-name, bad-continuation

de_string = Struct(
    Const(b"\x60\x0A"),
    "length"/Int16ul,
    "value"/Bytes(lambda ctx: ctx.length)
)

separator = Const(b"\xa3_\x02\x00")

de = "de"/Struct(
    "version"/Float32l,
    "interval_version"/Int32ul,
    "game_options_version"/Int32ul,
    "dlc_count"/Int32ul,
    "dlc_ids"/Array(lambda ctx: ctx.dlc_count, Int32ul),
    "dataset_ref"/Int32ul,
    Peek("difficulty_id"/Int32ul),
    DifficultyEnum("difficulty"/Int32ul),
    "selected_map_id"/Int32ul,
    "resolved_map_id"/Int32ul,
    "reveal_map"/Int32ul,
    Peek("victory_type_id"/Int32ul),
    VictoryEnum("victory_type"/Int32ul),
    Peek("starting_resources_id"/Int32ul),
    ResourceLevelEnum("starting_resources"/Int32ul),
    "starting_age_id"/Int32ul,
    "starting_age"/AgeEnum(Computed(lambda ctx: ctx.starting_age_id - 2)),
    "ending_age_id"/Int32ul,
    "ending_age"/AgeEnum(Computed(lambda ctx: ctx.ending_age_id - 2)),
    "game_type"/Int32ul,
    separator,
    separator,
    "speed"/Float32l,
    "treaty_length"/Int32ul,
    "population_limit"/Int32ul,
    "num_players"/Int32ul,
    "unused_player_color"/Int32ul,
    "victory_amount"/Int32ul,
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
    "turbo_enabled"/Flag,
    "shared_exploration"/Flag,
    "team_positions"/Flag,
    If(lambda ctx: find_save_version(ctx) >= 13.34, Bytes(8)),
    separator,
    "players"/Array(8, Struct(
        "dlc_id"/Int32ul,
        "color_id"/Int32sl,
        "selected_color"/Byte,
        "selected_team_id"/Byte,
        "resolved_team_id"/Byte,
        "dat_crc"/Bytes(8),
        "mp_game_version"/Byte,
        "civ_id"/Byte,
        Const(b"\x00\x00\x00"),
        "ai_type"/de_string,
        "ai_civ_name_index"/Byte,
        "ai_name"/de_string,
        "name"/de_string,
        "type"/PlayerTypeEnum(Int32ul),
        "profile_id"/Int32ul,
        Const(b"\x00\x00\x00\x00"),
        "player_number"/Int32sl,
        "hd_rm_elo"/Int32ul,
        "hd_dm_elo"/Int32ul,
        "animated_destruction_enabled"/Flag,
        "custom_ai"/Flag
    )),
    "fog_of_war"/Flag,
    "cheat_notifications"/Flag,
    "colored_chat"/Flag,
    Bytes(9),
    separator,
    Bytes(12),
    If(lambda ctx: ctx._.save_version >= 13.13, Bytes(5)),
    "strings"/Array(23,
        Struct(
            "string"/de_string,
            RepeatUntil(lambda x, lst, ctx: lst[-1] not in [3, 21, 23, 42, 44, 45, 46], Int32ul)
        )
    ),
    "strategic_numbers"/Array(59, Int32sl),
    "num_ai_files"/Int64ul,
    "ai_files"/Array(lambda ctx: ctx.num_ai_files, Struct(
        Bytes(4),
        "name"/de_string,
        Bytes(4),
    )),
    "guid"/Bytes(16),
    "lobby_name"/de_string,
    "modded_dataset"/de_string,
    Bytes(19),
    If(lambda ctx: ctx._.save_version >= 13.13, Bytes(5)),
    If(lambda ctx: ctx._.save_version >= 13.17, Bytes(9)),
    If(lambda ctx: ctx._.save_version >= 20.06, Bytes(1)),
    If(lambda ctx: ctx._.save_version >= 20.16, Bytes(8)),
    de_string,
    Bytes(5),
    If(lambda ctx: ctx._.save_version >= 13.13, Byte),
    If(lambda ctx: ctx._.save_version < 13.17, Struct(
        de_string,
        Int32ul,
        Bytes(4), # usually zero
    )),
    If(lambda ctx: ctx._.save_version >= 13.17, Bytes(2))
)
