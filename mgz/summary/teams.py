"""Determine teams."""


def get_teams_data(header):
    """Get teams."""
    teams = []
    for j, player in enumerate(header.initial.players):
        added = False
        for i in range(0, len(header.initial.players)):
            if player.attributes.my_diplomacy[i] == 'ally':
                inner_team = False
                outer_team = False
                new_team = True
                for k, members in enumerate(teams):
                    if j in members or i in members:
                        new_team = False
                    if j in members and i not in members:
                        inner_team = k
                        break
                    if j not in members and i in members:
                        outer_team = k
                        break
                if new_team:
                    teams.append([i, j])
                if inner_team is not False:
                    teams[inner_team].append(i)
                if outer_team is not False:
                    teams[outer_team].append(j)
                added = True
        if not added and j != 0:
            teams.append([j])
    return teams
