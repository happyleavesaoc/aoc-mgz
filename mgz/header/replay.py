from construct import *
from mgz.enums import *

"""Basic information about the recorded game"""
replay = "replay"/Struct(
    Padding(12),
    GameSpeedEnum("game_speed"/Int32ul),
    Padding(8),
    "game_speed_float"/Float32l, # 1.0, 1.5, or 2.0
    Padding(17),
    "rec_player"/Int16ul, # id of the rec owner
    "num_players"/Byte, # including gaia
    Const(b"\x00\x00\x00\x00"),
    Padding(58),
)
