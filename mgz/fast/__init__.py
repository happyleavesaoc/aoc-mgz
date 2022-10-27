"""Fast(er) parsing for situations requiring speed."""
import io
import struct

from mgz.fast.enums import Operation, Action, Postgame
from mgz.fast.actions import parse_action_71094
from mgz.util import check_flags, unpack


CHECKSUM_INTERVAL = 500


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
    x, y, _ = struct.unpack('<ffI', data.read(12))
    return x, y


def parse_action(action_type, data):
    """Parse player, objects, and coordinates from actions."""
    player_id, length = struct.unpack_from('<bh', data)
    if len(data) == length + 3:
        return parse_action_71094(action_type, player_id, data[3:])
    if action_type == Action.RESIGN:
        return dict(player_id=data[0])
    if action_type == Action.TRIBUTE:
        player_id, player_id_to, resource_id, amount, fee = struct.unpack_from('<bbbff', data)
        return dict(player_id=player_id, player_id_to=player_id_to, resource_id=resource_id, amount=amount, fee=fee)
    if action_type == Action.DE_TRIBUTE:
        player_id, player_id_to, unknown_byte, unknown_int, wood, food, gold, stone = struct.unpack_from('<bbbiffff', data)
        return dict(player_id=player_id,
                    player_id_to=player_id_to,
                    food=food,
                    wood=wood,
                    stone=stone,
                    gold=gold)
    if action_type == Action.MOVE:
        player_id, selected, x, y = struct.unpack_from('<b6xI2f', data)
        object_ids = []
        if selected != 255:
            offset = 0
            if check_flags(struct.unpack_from('<4b', data[19:])):
                offset = 4
            object_ids = struct.unpack_from('<' + str(selected) + 'I', data[19 + offset:])
        return dict(player_id=player_id, x=x, y=y, object_ids=list(object_ids))
    if action_type == Action.CREATE:
        player_id, x, y = struct.unpack_from('<3xhx2f', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.ORDER:
        player_id, target_id, selected, x, y = struct.unpack_from('<b2xIh2x2f', data)
        object_ids = []
        if selected != 255:
            offset = 0
            if check_flags(struct.unpack_from('<4b', data[19:])):
                offset = 4
            object_ids = struct.unpack_from('<' + str(selected) + 'I', data[19 + offset:])
        return dict(player_id=player_id, target_id=target_id, x=x, y=y, object_ids=list(object_ids))
    if action_type == Action.BUILD:
        player_id, x, y, building_id = struct.unpack_from('<xh2fI', data)
        return dict(player_id=player_id, x=x, y=y, building_id=building_id)
    if action_type == Action.STANCE:
        stance_id, *object_ids = struct.unpack_from('<xb' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), stance_id=stance_id)
    if action_type == Action.RESEARCH:
        object_id, player_id = struct.unpack_from('<3xIh', data)
        if len(data) >= 19:
            technology_id, = struct.unpack_from('<I', data[11:15])
        else:
            technology_id, = struct.unpack_from('<h', data[9:11])
        return dict(player_id=player_id, technology_id=technology_id, object_ids=[object_id])
    if action_type == Action.FORMATION:
        player_id, formation_id, *object_ids = struct.unpack_from('<xhI' + str(data[0]) + 'I', data)
        return dict(player_id=player_id, object_ids=list(object_ids), formation_id=formation_id)
    if action_type == Action.QUEUE:
        object_id, unit_id, amount = struct.unpack_from('<3xIhh', data)
        return dict(object_ids=[object_id], unit_id=unit_id, amount=amount)
    if action_type == Action.GATHER_POINT:
        target_id, x, y, *object_ids = struct.unpack_from('<3xi4x2f' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y, target_id=target_id)
    if action_type == Action.MULTIQUEUE:
        unit_id, amount, *object_ids = struct.unpack_from('<3xhxb' + str(data[5]) + 'I', data)
        return dict(object_ids=object_ids, unit_id=unit_id, amount=amount)
    if action_type == Action.PATROL:
        x, y, *object_ids = struct.unpack_from('<3xf36xf36x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.SPECIAL:
        target_id, order_id, x, y, *flags = struct.unpack_from('<3xib3x2f4x4b', data)
        offset = 0
        if check_flags(flags):
            offset = 4
        object_ids = struct.unpack_from('<' + str(data[0]) + 'I', data[23 + offset:])
        values = dict(object_ids=list(object_ids), order_id=order_id)
        if x > 0 and y > 0:
            values.update(dict(x=x, y=y))
        if target_id > 0:
            values.update(dict(target_id=target_id))
        return values
    if action_type == Action.BACK_TO_WORK:
        object_id, = struct.unpack_from('<3xI', data)
        return dict(object_ids=[object_id])
    if action_type == Action.UNGARRISON:
        selected, = struct.unpack_from('<h', data)
        x, y, *object_ids = struct.unpack_from('<3x2f8x' + str(selected) + 'I', data)
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
        selection_count, = struct.unpack_from('b', data)
        offset = len(data) - selection_count * 4

        if offset > 15:
            # In DE recordings all coordinates are prefixed with a zero.
            player_id, x_start, y_start, x_end, y_end, building_id, z1, const = struct.unpack_from(
                '<bxbxbxbxbx2h1i', data, offset=1)
        else:
            player_id, x_start, y_start, x_end, y_end, building_id, z1, const = struct.unpack_from(
                '<5bx2h1i', data, offset=1)

        object_ids = struct.unpack_from('<' + str(selection_count) + 'I', data[offset:])

        return dict(player_id=player_id,
                    x=x_start,
                    y=y_start,
                    x_end=x_end,
                    y_end=y_end,
                    building_id=building_id,
                    object_ids=object_ids)

    if action_type == Action.GAME:
        return dict(player_id=data[1], command_id=data[0])
    if action_type == Action.FLARE:
        x, y, player_id = struct.unpack_from('<19x2fb', data)
        return dict(player_id=player_id, x=x, y=y)
    if action_type == Action.REPAIR:
        target_id, *flags = struct.unpack_from('<3xI4b', data)
        offset = 0
        if check_flags(flags):
            offset = 4
        object_ids = struct.unpack_from('<' + str(data[0]) + 'I', data[7 + offset:])
        return dict(target_id=target_id, object_ids=list(object_ids))
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
    if action_type == Action.ATTACK_GROUND:
        object_ids = []
        selected, x, y, *flags = struct.unpack_from('<b2x2f4b', data)
        offset = 0
        if check_flags(flags):
            offset = 4
        if selected > 0:
            object_ids = struct.unpack_from('<' + str(selected) + 'I', data[11 + offset:])
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.ADD_WAYPOINT:
        object_ids = []
        selected, x, y = struct.unpack_from('<xb2b', data)
        if selected > 0:
            object_ids = struct.unpack_from('<4x' + str(selected) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.DE_QUEUE:
        player_id, unit_id, amount, *object_ids = struct.unpack_from('<b4xhbx' + str(data[3]) + 'I', data)
        return dict(player_id=player_id, object_ids=object_ids, amount=amount, unit_id=unit_id)
    if action_type == Action.DE_ATTACK_MOVE:
        x, y, *object_ids = struct.unpack_from('<3xf36xf36x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids), x=x, y=y)
    if action_type == Action.DE_AUTOSCOUT:
        object_ids = struct.unpack_from('<x' + str(data[0]) + 'I', data)
        return dict(object_ids=list(object_ids))
    return dict()


def action(data, sequence=None):
    """Handle actions."""
    length, = struct.unpack('<I', data.read(4))
    action_id = int.from_bytes(data.read(1), 'little')
    action_bytes = data.read(length - 1)
    if sequence is None:
       sequence, = struct.unpack('<I', data.read(4))
    action_type = Action(action_id)
    if action_type == Action.POSTGAME:
        payload = dict(bytes=action_bytes + data.read())
    else:
        try:
            payload = parse_action(action_type, action_bytes)
        except struct.error:
            return Action.ERROR, {}
    payload["sequence"] = sequence
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
    if a != 0:  # AOC 1.0x
        data.seek(-12, 1)
    if b == 2:  # DE
        data.seek(-8, 1)


def save(data):
    """Handle saved chapter."""
    data.seek(-4, 1)
    pos = data.tell()
    length, _ = struct.unpack('<II', data.read(8))
    data.read(length - pos - 8)


def postgame(data):
    """Handle DE postgame."""
    data = io.BytesIO(data.read()[::-1])
    data.read(8)
    version, num_blocks = struct.unpack('>II', data.read(8))
    out = {}
    for _ in range(0, num_blocks):
        identifier, length = struct.unpack('>II', data.read(8))
        block = io.BytesIO(data.read(length)[::-1])
        postgame_type = Postgame(identifier)
        if postgame_type == Postgame.WORLD_TIME:
            out['world_time'] = struct.unpack('<I', block.read(4))[0]
        elif postgame_type == Postgame.LEADERBOARDS:
            num_leaderboards = struct.unpack('<I', block.read(4))[0]
            leaderboards = []
            for lb in range(0, num_leaderboards):
                leaderboard_id, unk = struct.unpack('<IH', block.read(6))
                num_players = struct.unpack('<I', block.read(4))[0]
                player_data = []
                for i in range(0, num_players):
                    player_num, rank, rating = struct.unpack('<3i', block.read(12))
                    player_data.append({
                        'number': player_num,
                        'rank': rank,
                        'rating': rating
                    })
                leaderboards.append({
                    'id': leaderboard_id,
                    'players': player_data
                })
            out['leaderboards'] = leaderboards
        else:
            raise RuntimeError("unparsed postgame block")
    return out


def meta(data):
    """Handle log meta."""
    try:
        first, = struct.unpack('<I', data.read(4))
        if first != 500:  # Not AOK
            data.read(4)
        data.read(20)
        a, b, _ = struct.unpack('<III', data.read(12))
        if a != 0:  # AOC 1.0x
            data.seek(-12, 1)
        if b == 2:  # DE
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
        if op_type == Operation.POSTGAME:
            return op_type, postgame(data)
    except struct.error:
        raise EOFError
    raise RuntimeError("unknown data received")
