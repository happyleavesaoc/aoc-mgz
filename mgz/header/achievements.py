"""Achievements."""

from construct import Array, Float32l, Int32ul, Padding, Struct

# pylint: disable=invalid-name


# Achievements snapshot taken at the start of the recorded game, not the end.
player_achievements = "ach"/Struct(
    Padding(13),
    "total_points"/Int32ul,
    Padding(26),
    "war_points"/Int32ul,
    Padding(34),
    "num_kills"/Float32l,
    Padding(28),
    "num_killed"/Float32l,
    Padding(28),
    "num_killed2"/Float32l,
    Padding(284),
    Padding(4),
    Padding(60),
    Padding(4),
    Padding(444),
    "total_food"/Float32l,
    Padding(28),
    "total_wood"/Float32l,
    Padding(28),
    "total_stone"/Float32l,
    Padding(28),
    "total_gold"/Float32l,
    Padding(444),
    "max_villagers"/Float32l,
    Padding(28),
    "max_villagers2"/Float32l,
    Padding(28),
    "relic_castle"/Float32l,
    Padding(28),
    "relic_castle2"/Float32l,
    Padding(28),
    "wonder"/Float32l,
    Padding(28),
    "relic_gold"/Float32l,
    Padding(124),
    "researched_techs"/Float32l,
    Padding(28),
    "explored_percent"/Float32l,
    Padding(4),
)

"""Achievements exist for all players but Gaia"""
achievements = Array(lambda ctx: ctx.replay.num_players - 1, player_achievements)
