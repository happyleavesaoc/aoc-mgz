"""Fast(er) parsing for situations requiring speed."""
import struct
from enum import Enum

CHECKSUM_INTERVAL = 500


class Operation(Enum):
    """Operation types."""
    ACTION = 1
    SYNC = 2
    VIEWLOCK = 3
    CHAT = 4
    START = 5
    SAVE = 6

class Action(Enum):
    """Action types."""
    ORDER = 0
    STOP = 1
    WORK = 2
    MOVE = 3
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
    AI_COMMAND = 53
    MAKE = 100
    RESEARCH = 101
    BUILD = 102
    GAME = 103
    WALL = 105
    DELETE = 106
    ATTACK_GROUND = 107
    TRIBUTE = 108
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
    POSTGAME = 255


def sync(data):
    """Handle synchronizations."""
    increment, marker = struct.unpack('<II', data.read(8))
    data.seek(-4, 1)
    checksum = None
    if marker == 0:
        data.read(8)
        checksum, = struct.unpack('<I', data.read(4))
        data.read(4)
        seq, = struct.unpack('<I', data.read(4))
        if seq > 0:
            data.read(332)
        data.read(8)
    return increment, checksum


def viewlock(data):
    """Handle viewlocks."""
    data.read(12)


def action(data):
    """Handle actions."""
    length, = struct.unpack('<I', data.read(4))
    action_id = int.from_bytes(data.read(1), 'little')
    action_bytes = data.read(length - 1)
    data.read(4)
    payload = {}
    action_type = Action(action_id)
    if action_type == Action.POSTGAME:
        payload['bytes'] = action_bytes + data.read()
    elif action_type == Action.RESIGN:
        payload['player_id'] = action_bytes[0]
    return action_type, payload


def chat(data):
    """Handle chat."""
    check, length = struct.unpack('<II', data.read(8))
    if check == CHECKSUM_INTERVAL:
        data.seek(-4, 1)
        start(data)
        return None
    msg = data.read(length)
    return msg


def start(data):
    """Handle start."""
    return data.read(28)


def save(data):
    """Handle saved chapter."""
    data.seek(-4, 1)
    pos = data.tell()
    length, _ = struct.unpack('<II', data.read(8))
    data.read(length - pos - 8)


def operation(data):
    """Handle body operations."""
    try:
        op_id, = struct.unpack('<I', data.read(4))
        if op_id == CHECKSUM_INTERVAL: # AOK
            return Operation.START, data.read(32)
        try:
            op_type = Operation(op_id)
        except ValueError:
            return Operation.SAVE, save(data)
        if op_type == Operation.ACTION:
            return op_type, action(data)
        if op_type == Operation.SYNC:
            return op_type, sync(data)
        if op_type == Operation.VIEWLOCK:
            return op_type, viewlock(data)
        if op_type == Operation.CHAT:
            return op_type, chat(data)
        if op_type == Operation.START:
            return op_type, start(data)
    except struct.error:
        raise EOFError
    raise RuntimeError("unknown data received")
