"""Replay."""

from construct import Array, Byte, Flag, Float32l, Int16ul, Int32sl, Int32ul, Padding, Struct, If, Embedded

from mgz.util import Version

# pylint: disable=invalid-name


# Basic information about the recorded game
replay = "replay"/Struct(
    "old_time"/Int32ul,
    "world_time"/Int32ul,
    "old_world_time"/Int32ul,
    "game_speed_id"/Int32ul, # world_time_delta
    "world_time_delta_seconds"/Int32ul,
    "timer"/Float32l,
    "game_speed_float"/Float32l,
    "temp_pause"/Byte,
    "next_object_id"/Int32ul,
    "next_reusable_object_id"/Int32sl,
    "random_seed"/Int32ul,
    "random_seed_2"/Int32ul,
    "rec_player"/Int16ul, # id of the rec owner
    "num_players"/Byte, # including gaia
    Embedded(If(lambda ctx: ctx._.version != Version.AOK, Struct(
        "instant_build"/Flag,
        "cheats_enabled"/Flag
    ))),
    "game_mode"/Int16ul, # MP or SP?
    "campaign"/Int32ul,
    "campaign_player"/Int32ul,
    "campaign_scenario"/Int32ul,
    "king_campaign"/Int32ul,
    "king_campaign_player"/Byte,
    "king_campaign_scenario"/Byte,
    "player_turn"/Int32ul,
    "player_time_delta"/Array(9, "turn"/Int32ul),
    If(lambda ctx: ctx._.version == Version.DE, Padding(8))
)
