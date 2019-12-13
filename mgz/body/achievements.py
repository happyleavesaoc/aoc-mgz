"""UserPatch 1.4+ achievements - appended to recorded game."""

from construct import (Array, Byte, Flag, Int16ul, Int32sl, Int32ul, Padding,
                       Peek, Struct, Bytes)

from mgz.util import TimeSecAdapter

# pylint: disable=invalid-name


military = "military"/Struct(
    "score"/Int16ul,
    "units_killed"/Int16ul,
    "hit_points_killed"/Int16ul,
    "units_lost"/Int16ul,
    "buildings_razed"/Int16ul,
    "hit_points_razed"/Int16ul,
    "buildings_lost"/Int16ul,
    "units_converted"/Int16ul
)

economy = "economy"/Struct(
    "score"/Int16ul,
    Padding(2),
    "food_collected"/Int32ul,
    "wood_collected"/Int32ul,
    "stone_collected"/Int32ul,
    "gold_collected"/Int32ul,
    "tribute_sent"/Int16ul,
    "tribute_received"/Int16ul,
    "trade_gold"/Int16ul,
    "relic_gold"/Int16ul
)

technology = "technology"/Struct(
    "score"/Int16ul,
    Padding(2),
    Peek("feudal_time_int"/Int32sl),
    TimeSecAdapter("feudal_time"/Int32sl),
    Peek("castle_time_int"/Int32sl),
    TimeSecAdapter("castle_time"/Int32sl),
    Peek("imperial_time_int"/Int32sl),
    TimeSecAdapter("imperial_time"/Int32sl),
    "explored_percent"/Byte,
    "research_count"/Byte,
    "research_percent"/Byte
)

society = "society"/Struct(
    "score"/Int16ul,
    "total_wonders"/Byte,
    "total_castles"/Byte,
    "relics_captured"/Byte,
    Padding(1),
    "villager_high"/Int16ul,
)

achievements = "achievements"/Struct(
    "player_name"/Bytes(16),
    "total_score"/Int16ul,
    Array(8, "total_scores"/Int16ul),
    "victory"/Flag,
    "civilization"/Byte,
    "color_id"/Byte,
    "team"/Byte,
    "ally_count"/Byte,
    "random_civ"/Flag, # never actually set
    "mvp"/Flag,
    Padding(3),
    "result"/Int32ul,
    military,
    Padding(32),
    economy,
    Padding(16),
    technology,
    Padding(1),
    society,
    Padding(84),
)
