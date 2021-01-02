"""Determine teams."""


def get_teams_data(header):
    """Get teams."""
    allies = {}
    for number, player in enumerate(header.initial.players[1:]):
        allies[number + 1] = set([number + 1])
        for i, mode in enumerate(player.attributes.my_diplomacy):
            if mode == 'ally':
                allies[number + 1].add(i)
    return set([frozenset(s) for s in allies.values()])
