"""Determine teams."""
from collections import defaultdict

def get_teams_data(header):
    """Get teams."""
    if header.de:
        # 0: empty slot
        # 1: no team
        # n: n - 1 = team number
        by_team = defaultdict(list)
        for id, player in enumerate(header.de.players):
            if player.resolved_team_id > 1:
                by_team[player.resolved_team_id].append(id + 1)
            elif player.resolved_team_id == 1:
                by_team[id + 9].append(id + 1)
        return set([frozenset(s) for s in by_team.values()])
    allies = {}
    for number, player in enumerate(header.initial.players[1:]):
        allies[number + 1] = set([number + 1])
        for i, mode in enumerate(player.attributes.my_diplomacy):
            if mode == 'ally':
                allies[number + 1].add(i)
    return set([frozenset(s) for s in allies.values()])
