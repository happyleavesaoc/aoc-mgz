from construct import (
    Struct, Int32ul, Float32l, Array, Padding, Flag, If,
    Byte, Int16ul, Bytes, Int32sl, Peek, Const, RepeatUntil,
    Int64ul, Computed, Embedded, IfThenElse
)

from mgz.enums import VictoryEnum, ResourceLevelEnum, AgeEnum, PlayerTypeEnum, DifficultyEnum
from mgz.util import find_save_version

separator = Const(b"\xa3_\x02\x00")

hd_string = Struct(
    "length"/Int16ul,
    Const(b"\x60\x0A"),
    "value"/Bytes(lambda ctx: ctx.length)
)

test_57 = "test_57"/Struct(
    "check"/Int32ul,
    Padding(4),
    If(lambda ctx: ctx._._.version >= 1006, Bytes(1)),
    Padding(15),
    hd_string,
    Padding(1),
    If(lambda ctx: ctx._._.version >= 1005, hd_string),
    hd_string,
    Padding(16),
    "test"/Int32ul,
    "is_57"/Computed(lambda ctx: ctx.check == ctx.test)
)

player = Struct(
    "dlc_id"/Int32ul,
    "color_id"/Int32ul,
    "unk1_1006"/If(lambda ctx: ctx._._.version >= 1006, Bytes(1)),
    "unk"/Bytes(2),
    "dat_crc"/Bytes(4),
    "mp_game_version"/Byte,
    "team_index"/Int32ul,
    "civ_id"/Int32ul,
    "ai_type"/hd_string,
    "ai_civ_name_index"/Byte,
    "ai_name"/If(lambda ctx: ctx._._.version >= 1005, hd_string),
    "name"/hd_string,
    "type"/PlayerTypeEnum(Int32ul),
    "steam_id"/Int64ul,
    "player_number"/Int32sl,
    Embedded(If(lambda ctx: ctx._._.version >= 1006 and not ctx._.test_57.is_57, Struct(
        "hd_rm_rating"/Int32ul,
        "hd_dm_rating"/Int32ul,
    )))
)

hd = "hd"/Struct(
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
    "starting_age"/AgeEnum(Computed(lambda ctx: ctx.starting_age_id)),
    "ending_age_id"/Int32ul,
    "ending_age"/AgeEnum(Computed(lambda ctx: ctx.ending_age_id)),
    "game_type"/If(lambda ctx: ctx.version >= 1006, Int32ul),
    separator,
    "ver1000"/If(lambda ctx: ctx.version == 1000, Struct(
        "map_name"/hd_string,
        "unk"/hd_string
    )),
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
    "unk"/Bytes(1),
    Embedded(IfThenElse(lambda ctx: ctx.version == 1000,
        Struct(
            Bytes(40*3),
            separator,
            Bytes(40),
            "strings"/Array(8, hd_string),
            Bytes(16),
            separator,
            Bytes(10),
        ),
        Struct(
            Peek(test_57),
            "players"/Array(8, player),
            "fog_of_war"/Flag,
            "cheat_notifications"/Flag,
            "colored_chat"/Flag,
            Bytes(9),
            separator,
            "is_ranked"/Flag,
            "allow_specs"/Flag,
            "lobby_visibility"/Int32ul,
            "custom_random_map_file_crc"/Int32ul,
            "custom_scenario_or_campaign_file"/hd_string,
            Bytes(8),
            "custom_random_map_file"/hd_string,
            Bytes(8),
            "custom_random_map_scenarion_file"/hd_string,
            Bytes(8),
            "guid"/Bytes(16),
            "lobby_name"/hd_string,
            "modded_dataset"/hd_string,
            "modded_dataset_workshop_id"/Bytes(4),
            If(lambda ctx: ctx._.version >= 1005,
                Struct(
                    Bytes(4),
                    hd_string,
                    Bytes(4)
                )
            )
        )
    ))
)
