"""Determine diplomacy type."""


def get_diplomacy_data(header, teams):
    """Compute diplomacy."""
    player_num = 0
    computer_num = 0
    for player in header.scenario.game_settings.player_info:
        if player.type == 'human':
            player_num += 1
        elif player.type == 'computer':
            computer_num += 1
    total_num = player_num + computer_num

    diplomacy = {
        'FFA': (len(teams) == total_num) and total_num > 2,
        'TG':  len(teams) == 2 and total_num > 2,
        '1v1': total_num == 2,
    }

    diplomacy['type'] = 'Other'
    team_sizes = sorted([len(team) for team in teams])
    diplomacy['team_size'] = 'v'.join([str(size) for size in team_sizes])
    if diplomacy['FFA']:
        diplomacy['type'] = 'FFA'
        diplomacy['team_size'] = 'FFA'
    elif diplomacy['TG']:
        diplomacy['type'] = 'TG'
    elif diplomacy['1v1']:
        diplomacy['type'] = '1v1'
    return diplomacy
