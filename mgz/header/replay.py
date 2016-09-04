from construct import *
from mgz.enums import *

"""Basic information about the recorded game"""
replay = Struct("replay",
    Padding(12),
    GameSpeedEnum(ULInt32("game_speed")),
    Padding(8),
    LFloat32("game_speed_float"), # 1.0, 1.5, or 2.0
    Padding(17),
    ULInt16("rec_player"), # id of the rec owner
    Byte("num_players"), # including gaia
    Const("\x00\x00\x00\x00"),
    Padding(58),
)
