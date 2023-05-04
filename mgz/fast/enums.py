"""Fast body parser enumerations."""

from enum import Enum

class Operation(Enum):
    """Operation types."""
    ACTION = 1
    SYNC = 2
    VIEWLOCK = 3
    CHAT = 4
    START = 5
    POSTGAME = 6
    SAVE = 7


class Action(Enum):
    """Action types."""
    ERROR = -1
    ORDER = 0
    STOP = 1
    WORK = 2
    MOVE = 3
    CREATE = 4
    ADD_ATTRIBUTE = 5
    GIVE_ATTRIBUTE = 6
    AI_ORDER = 10
    RESIGN = 11
    SPECTATE = 15
    ADD_WAYPOINT = 16
    STANCE = 18
    GUARD = 19
    FOLLOW = 20
    PATROL = 21
    FORMATION = 23
    SAVE = 27
    GROUP_MULTI_WAYPOINTS = 31
    CHAPTER = 32
    DE_ATTACK_MOVE = 33
    HD_UNKNOWN_34 = 34
    DE_RETREAT = 35
    DE_UNKNOWN_37 = 37
    DE_AUTOSCOUT = 38
    DE_UNKNOWN_39 = 39
    DE_UNKNOWN_40 = 40
    DE_TRANSFORM = 41
    RATHA_ABILITY = 43
    AI_COMMAND = 53
    DE_UNKNOWN_80 = 80
    MAKE = 100
    RESEARCH = 101
    BUILD = 102
    GAME = 103
    WALL = 105
    DELETE = 106
    ATTACK_GROUND = 107
    TRIBUTE = 108
    DE_UNKNOWN_109 = 109
    REPAIR = 110
    UNGARRISON = 111
    MULTIQUEUE = 112
    GATE = 114
    FLARE = 115
    SPECIAL = 117
    QUEUE = 119
    GATHER_POINT = 120
    SELL = 122
    BUY = 123
    DROP_RELIC = 126
    TOWN_BELL = 127
    BACK_TO_WORK = 128
    DE_QUEUE = 129
    DE_UNKNOWN_130 = 130
    DE_UNKNOWN_131 = 131
    DE_UNKNOWN_135 = 135
    DE_UNKNOWN_136 = 136
    DE_UNKNOWN_138 = 138
    DE_TRIBUTE = 196
    POSTGAME = 255


class Postgame(Enum):
    """Postgame types."""
    WORLD_TIME = 1
    LEADERBOARDS = 2
