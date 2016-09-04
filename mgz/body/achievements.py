from construct import *
from mgz.util import TimeSecAdapter

"""UserPatch 1.4 achievements - appended to recorded game"""

military = Struct("military",
    ULInt16("score"),
    ULInt16("units_killed"),
    Padding(2),
    ULInt16("units_lost"),
    ULInt16("buildings_razed"),
    Padding(2),
    ULInt16("buildings_lost"),
    ULInt16("units_converted")
)

economy = Struct("economy",
    ULInt16("score"),
    Padding(2),
    ULInt32("food_collected"),
    ULInt32("wood_collected"),
    ULInt32("stone_collected"),
    ULInt32("gold_collected"),
    ULInt16("tribute_sent"),
    ULInt16("tribute_received"),
    ULInt16("trade_gold"),
    ULInt16("relic_gold")
)

technology = Struct("technology",
    ULInt16("score"),
    Padding(2),
    TimeSecAdapter(ULInt32("feudal_time")),
    TimeSecAdapter(ULInt32("castle_time")),
    TimeSecAdapter(ULInt32("imperial_time")),
    Byte("explored_percent"),
    Byte("research_count"),
    Byte("research_percent")
)

society = Struct("society",
    ULInt16("score"),
    Byte("total_wonders"),
    Byte("total_castles"),
    Byte("relics_captured"),
    Padding(1),
    ULInt16("villager_high"),
)

achievements = Struct("achievements",
    String("player_name", 16, padchar = '\x00', trimdir = 'right'),
    ULInt16("total_score"),
    Array(8, ULInt16("total_scores")),
    Byte("victory"),
    Byte("civilization"),
    Byte("color_id"),
    Byte("team"),
    Padding(2),
    Byte("medal"),
    Padding(3),
    Byte("result"),
    Padding(3),
    military,
    Padding(32),
    economy,
    Padding(16),
    technology,
    Padding(1),
    society,
    Padding(84),
)
