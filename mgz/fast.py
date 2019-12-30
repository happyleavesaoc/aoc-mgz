"""Fast(er) parsing for situations requiring speed."""
import struct
from enum import Enum


class Operation(Enum):
    """Operation types."""
    ACTION = 1
    SYNC = 2
    VIEWLOCK = 3
    CHAT = 4
    START = 5


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
    type_id = int.from_bytes(data.read(1), 'little')
    action_bytes = data.read(length - 1)
    data.read(4)
    payload = {}
    if type_id == 255: # postgame
        payload['bytes'] = action_bytes + data.read()
    elif type_id == 11: # resign
        payload['player_id'] = action_bytes[0]
    return type_id, payload


def chat(data):
    """Handle chat."""
    check, length = struct.unpack('<II', data.read(8))
    if check == 500:
        data.seek(-4, 1)
        start(data)
        return None
    msg = data.read(length)
    return msg


def start(data):
    """Handle start."""
    data.read(28)


def operation(data):
    """Handle body operations."""
    try:
        op_id, = struct.unpack('<I', data.read(4))
    except struct.error:
        raise EOFError
    op_type = Operation(op_id)
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
    raise RuntimeError('unknown data encountered')
