"""Replay."""

from construct import Byte, Flag, Float32l, Int16ul, Int32ul, Padding, Struct

# pylint: disable=invalid-name


# Basic information about the recorded game
replay = "replay"/Struct(
    Padding(12),
    "game_speed"/Int32ul,
    Padding(8),
    "game_speed_float"/Float32l,
    Padding(17),
    "rec_player"/Int16ul, # id of the rec owner
    "num_players"/Byte, # including gaia
    "instant_build"/Flag,
    "cheats_enabled"/Flag,
    "game_mode"/Int16ul, # MP or SP?
    Padding(58)
)
