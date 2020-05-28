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
    CREATE = 4
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
    DE_AUTOSCOUT = 38
    DE_UNKNOWN_39 = 39
    DE_UNKNOWN_41 = 41
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


def parse_action(action_type, data):
    """Parse player, objects, and coordinates from actions."""
    if action_type == Action.RESIGN:
        return dict(player_id=data[0])
    if action_type == Action.TRIBUTE:
        player_id, player_id_to, resource_id, amount, fee = struct.unpack_from('<bbbff', data)
        return dict(player_id=player_id, player_id_to=player_id_to, resource_id=resource_id, amount=amount, fee=fee)
    if action_type == Action.MOVE:
        player_id, x, y = struct.unpack_from('<b10x2f', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.CREATE:
        player_id, x, y = struct.unpack_from('<3xhx2f', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.ORDER:
        player_id, x, y = struct.unpack_from('<b10x2f', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.BUILD:
        player_id, x, y, building_id = struct.unpack_from('<xh2fI', data)
        return dict(player_id=player_id, x=x, y=y, building_id=building_id)
    if action_type == Action.STANCE:
        object_ids = struct.unpack_from('<xx' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids))
    if action_type == Action.RESEARCH:
        object_id, player_id, technology_id = struct.unpack_from('<3xIh2xI', data)
        return dict(player_id=player_id, technology_id=technology_id, object_ids=[object_id])
    if action_type == Action.FORMATION:
        player_id, formation_id, (*object_ids) = struct.unpack_from('<xhI' + str(data[0]) + 'I', data)
        return dict(player_id=player_id, object_ids=list(object_ids), formation_id=formation_id)
    if action_type == Action.QUEUE:
        object_id, = struct.unpack_from('<3xI', data)
        return dict(object_ids=[object_id])
    if action_type == Action.GATHER_POINT:
        _, x, y, (*object_ids) = struct.unpack_from('<3xI4x2f' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.MULTIQUEUE:
        object_ids = struct.unpack_from('<7x' + str(data[5]) + 'I', data)
        return dict(object_ids=list(object_ids))
    if action_type == Action.PATROL:
        x, y, (*object_ids) = struct.unpack_from('<3xf36xf36x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.SPECIAL: # does not support DE
        _, x, y, (*object_ids) = struct.unpack_from('<3xi4x2f4x' + str(data[0]) + 'I', data)
        if x > 0 and y > 0:
            return dict(x=x, y=y, object_ids=list(object_ids))
        return dict(object_ids=list(object_ids))
    if action_type == Action.BACK_TO_WORK:
        object_id, = struct.unpack_from('<3xI', data)
        return dict(object_ids=[object_id])
    if action_type == Action.UNGARRISON:
        selected, = struct.unpack_from('<h', data)
        x, y, (*object_ids) = struct.unpack_from('<3x2f8x' + str(selected) + 'I', data)
        if x > 0 and y > 0:
            return dict(object_ids=list(object_ids), x=x, y=y)
        return dict(object_ids=list(object_ids))
    if action_type == Action.BUY:
        player_id, resource_id, amount = struct.unpack_from('<bbb', data)
        return dict(player_id=player_id, resource_id=resource_id, amount=amount)
    if action_type == Action.SELL:
        player_id, resource_id, amount = struct.unpack_from('<bbb', data)
        return dict(player_id=player_id, resource_id=resource_id, amount=amount)
    if action_type == Action.DELETE:
        object_id, player_id = struct.unpack_from('<3x2I', data)
        return dict(player_id=player_id, object_ids=[object_id])
    if action_type == Action.TOWN_BELL:
        object_id, = struct.unpack_from('<3xI', data)
        return dict(object_ids=[object_id])
    if action_type == Action.WALL:
        player_id, x, y = struct.unpack_from('<x3b', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.GAME:
        return dict(player_id=data[1], mode_id=data[0])
    if action_type == Action.FLARE:
        x, y, player_id = struct.unpack_from('<19x2fb', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.REPAIR: # does not support DE
        object_ids = struct.unpack_from('<7x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids))
    if action_type == Action.STOP:
        object_ids = struct.unpack_from('<x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids))
    if action_type == Action.GATE:
        object_id, = struct.unpack_from('<3xI', data)
        return dict(object_ids=[object_id])
    if action_type == Action.FOLLOW:
        object_ids = struct.unpack_from('<7x' + str(data[0]) + 'I', data)
        return dict(object_ids=object_ids)
    if action_type == Action.GUARD:
        object_ids = struct.unpack('<7x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids))
    if action_type == Action.ATTACK_GROUND: # does not support DE
        object_ids = []
        selected, x, y = struct.unpack_from('<b2x2f', data)
        if selected > 0:
            object_ids = struct.unpack_from('<11x' + str(selected) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.ADD_WAYPOINT:
        object_ids = []
        selected, x, y = struct.unpack_from('<xb2b', data)
        if selected > 0:
            object_ids = struct.unpack_from('<4x' + str(selected) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.DE_QUEUE:
        player_id, (*object_ids) = struct.unpack_from('<b8x' + str(data[3]) + 'I', data)
        return dict(player_id=player_id, object_ids=object_ids)
    if action_type == Action.DE_ATTACK_MOVE:
        x, y, (*object_ids) = struct.unpack_from('<3xf36xf36x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    return dict()


def action(data):
    """Handle actions."""
    length, = struct.unpack('<I', data.read(4))
    action_id = int.from_bytes(data.read(1), 'little')
    action_bytes = data.read(length - 1)
    data.read(4)
    action_type = Action(action_id)
    if action_type == Action.POSTGAME:
        payload = dict(bytes=action_bytes + data.read())
    else:
        payload = parse_action(action_type, action_bytes)
    return action_type, payload


def chat(data):
    """Handle chat."""
    _, length = struct.unpack('<II', data.read(8))
    msg = data.read(length)
    return msg


def start(data):
    """Handle start."""
    data.read(20)
    a, b, _ = struct.unpack('<III', data.read(12))
    if a != 0: # AOC 1.0x
        data.seek(-12, 1)
    if b == 2: # DE
        data.seek(-8, 1)


def save(data):
    """Handle saved chapter."""
    data.seek(-4, 1)
    pos = data.tell()
    length, _ = struct.unpack('<II', data.read(8))
    data.read(length - pos - 8)


def meta(data):
    """Handle log meta."""
    try:
        first, = struct.unpack('<I', data.read(4))
        if first != 500: # Not AOK
            data.read(4)
        data.read(20)
        a, b, _ = struct.unpack('<III', data.read(12))
        if a != 0: # AOC 1.0x
            data.seek(-12, 1)
        if b == 2: # DE
            data.seek(-8, 1)
    except struct.error:
        raise ValueError("insufficient meta received")


def operation(data):
    """Handle body operations."""
    try:
        op_id, = struct.unpack('<I', data.read(4))
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
    except struct.error:
        raise EOFError
    raise RuntimeError("unknown data received")
