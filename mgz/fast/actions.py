"""Action parsing for DE >= 71094."""
import io
import struct

from mgz.util import unpack, as_hex
from mgz.fast.enums import Action


def parse_action_71094(action_type, player_id, raw):
    data = io.BytesIO(raw)
    payload = {}
    if action_type is Action.RESIGN:
        unpack('<b', data)
    if action_type is Action.RESEARCH:
        object_id, selected, technology_id = unpack('<Ihh5x', data)
        selected_building_ids = unpack(f'<{selected}I', data, shorten=False)
        payload = dict(technology_id=technology_id, object_ids=[object_id])
    if action_type is Action.GAME:
        command_id = unpack('<h', data)
        payload = dict(command_id=command_id)
        if command_id == 0:
            source_player, target_player, mode_float, mode = unpack('<2xhhfb', data)
            payload.update(dict(target_player_id=target_player, diplomacy_mode=mode))
        elif command_id == 1:
            payload['speed'] = unpack('<6xf', data)
        elif command_id in [13, 14, 17, 18]:
            payload['number'] = unpack('<4xh', data)
    if action_type is Action.DE_QUEUE:
        selected, building_type, unit_id, amount, *object_ids = unpack('<h4xhhh4x', data)
        object_ids = list(unpack(f'<{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, amount=amount, unit_id=unit_id)
    if action_type is Action.MOVE:
        x, y, selected = unpack('<4x2fh', data)
        object_ids = []
        data.read(6)
        if selected > 0:
            object_ids = list(unpack(f'<{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, x=x, y=y)
    if action_type is Action.ORDER:
        target_id, x, y, selected = unpack('<I2fh', data)
        object_ids = []
        data.read(6)
        if selected > 0:
            object_ids = list(unpack(f'<{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, target_id=target_id, x=x, y=y)
    if action_type is Action.BUILD:
        selected, x, y, building_id, unk2, unk3, unk4 = unpack('<h2xffI8xhbb', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(building_id=building_id, object_ids=object_ids, x=x, y=y)
    if action_type is Action.GATHER_POINT:
        selected, x, y, target_id, target_type = unpack('<h2xffiix', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(target_id=target_id, target_type=target_type, x=x, y=y, object_ids=object_ids)
    if action_type is Action.DE_MULTI_GATHERPOINT:
        target_id, x, y = unpack('<iff', data) # This is a best guess. There is other unknown data in the payload.
        payload = dict(target_id=target_id, x=x, y=y)
    if action_type is Action.STANCE:
        selected, stance_id = unpack('<II', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(stance_id=stance_id, object_ids=object_ids)
    if action_type is Action.SPECIAL:
        selected, target_id, x, y, slot_id, order_id = unpack('<Iiff4xh2xh2x', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(order_id=order_id, slot_id=slot_id, target_id=target_id, x=x, y=y, object_ids=object_ids)
    if action_type is Action.FORMATION:
        selected, formation_id = unpack('<II', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(formation_id=formation_id, object_ids=object_ids)
    if action_type in [Action.BUY, Action.SELL]:
        resource_id, amount, object_id = unpack('<hhI', data)
        payload = dict(resource_id=resource_id, amount=amount, object_ids=[object_id])
    if action_type is Action.DE_TRANSFORM:
        # autoscout enable?
        object_id, y = unpack('<II', data)
        payload = dict(object_ids=[object_id])
    if action_type is Action.AI_ORDER:
        # used for autoscout moves
        # 01 00 00 00 75 06 00 00 ff ff ff ff 21 03 00 00 00 00 30 42 00 00 a0 42 00 00 00 00 00 00 80 3f 64 ff 01 00
        a, object_id, c, x, y = unpack('<II4xIff', data)
        payload = dict(object_ids=[object_id], x=x, y=y)
    if action_type in [Action.BACK_TO_WORK, Action.DELETE]:
        object_id = unpack('<I', data)
        payload = dict(object_ids=[object_id])
    if action_type is Action.WALL:
        selected, x1, y1, x2, y2, building_id = unpack('<IHHHHI', data)
        data.read(8)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, x=x1, y=y1, x_end=x2, y_end=y2, building_id=building_id)
    if action_type in [Action.PATROL, Action.DE_ATTACK_MOVE]:
        selected, x, y = unpack('<I4xf36xf36x', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, x=x, y=y)
    if action_type is Action.UNGARRISON:
        selected, x, y, target_id, unk = unpack('<IffiI', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, x=x, y=y, target_id=target_id)
    if action_type is Action.FLARE:
        x, y, num = unpack('<4xffb', data)
        targets = list(unpack(f'<{num}b', data, shorten=False))
        payload = dict(x=x, y=y, targets=targets)
    if action_type is Action.TOWN_BELL:
        building_id, mode = unpack('<Ib',data)
        payload = dict(building_id=building_id, mode=mode)
    if action_type is Action.STOP:
        selected = unpack('<I', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids)
    if action_type in [Action.FOLLOW, Action.GUARD]:
        selected, target_id = unpack('<II', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, target_id=target_id)
    if action_type is Action.ATTACK_GROUND:
        selected, x, y = unpack('<Iff', data)
        data.read(4)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, x=x, y=y)
    if action_type is Action.REPAIR:
        selected, target_id = unpack('<II', data)
        data.read(4)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids, target_id=target_id)
    if action_type is Action.DE_TRIBUTE:
        wood, food, gold, stone = unpack('<ffff', data)
        data.read(16) # cost[4]
        data.read(8) # attribute id[4]
        target_id = data.read(1)
        payload = dict(target_player_id=target_id, food=food, wood=wood, stone=stone, gold=gold)
    if action_type in [Action.GATE, Action.DROP_RELIC]:
        object_id = unpack('<I', data)
        payload = dict(object_ids=[object_id])
    if action_type in [Action.DE_AUTOSCOUT, Action.RATHA_ABILITY]:
        selected = unpack('<I', data)
        object_ids = list(unpack(f'{selected}I', data, shorten=False))
        payload = dict(object_ids=object_ids)
    if action_type is Action.MAKE:
        building_id, unit_id = unpack('<H6xh', data)
        payload = dict(building_id=building_id, unit_id=unit_id)
    return dict(player_id=player_id, **payload)
