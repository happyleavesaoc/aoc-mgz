"""Objects."""
from collections import defaultdict


TC_IDS = [71, 109, 141, 142]
STONE_WALL_ID = 117
PALISADE_WALL_ID = 72
CLIFFS = [264, 265, 266, 267, 268, 269, 270, 271, 272, 273]


def get_objects_data(header):
    """Get starting objects data."""
    objects = []
    tcs = defaultdict(int)
    stone_walls = {}
    palisade_walls = {}
    annexes = set()
    for player in header.initial.players:
        sleeping = []
        for o in player.sleeping_objects:
            if player.type == 2 and o.object_type not in CLIFFS:
                continue
            sleeping.append(o)
        for o in player.objects + sleeping:
            # static, moving, unit, and buildings only
            if o.type not in [10, 30, 70, 80]:
                continue
            # count town centers
            if o.object_type in TC_IDS:
                tcs[o.player_id] += 1
            # check for arena
            elif o.object_type == STONE_WALL_ID:
                stone_walls[o.player_id] = True
            # check for hideout
            elif o.object_type == PALISADE_WALL_ID:
                palisade_walls[o.player_id] = True
            # skip annexes
            if o.type == 80 and o.object_id in annexes:
                continue
            objects.append(dict(
                instance_id=o.object_id,
                object_id=o.object_type,
                class_id=o.type,
                player_number=o.player_id if o.player_id > 0 else None,
                x=o.x,
                y=o.y
            ))

    return dict(
        objects=objects,
        tcs=max(tcs.values()) if len(tcs.values()) > 0 else None,
        stone_walls=bool(stone_walls) and all(stone_walls.values()),
        palisade_walls=bool(palisade_walls) and all(palisade_walls.values())
    )
