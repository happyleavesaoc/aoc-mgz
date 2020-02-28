"""Determine player data."""


def ach(structure, fields):
    """Get field from achievements structure."""
    field = fields.pop(0)
    if structure:
        if hasattr(structure, field):
            structure = getattr(structure, field)
            if not fields:
                return structure
            return ach(structure, fields)
    return None


def get_achievements(postgame, name):
    """Get achievements for a player.

    Must match on name, not index, since order is not always the same.
    """
    if not postgame:
        return None
    for achievements in postgame.achievements:
        # achievements player name can be shorter
        if name.startswith(achievements.player_name.replace(b'\x00', b'')):
            return achievements
    return None


def guess_winner(teams, resigned, i):
    """Guess if a player won.

    Find what team the player was on. If anyone
    on their team resigned, assume the player lost.
    """
    for team in teams:
        if i not in team:
            continue
        for j in team:
            if j in resigned:
                return False
    return True


def get_players_data(header, postgame, teams, resigned, cheaters, profile_ids, ratings, encoding): # pylint: disable=too-many-arguments, too-many-locals
    """Get basic player info."""
    out = []
    for i, player in enumerate(header.initial.players[1:]):
        achievements = get_achievements(postgame, player.attributes.player_name)
        if achievements:
            winner = achievements.victory
        else:
            winner = guess_winner(teams, resigned, i + 1)
        feudal_time = ach(achievements, ['technology', 'feudal_time_int'])
        castle_time = ach(achievements, ['technology', 'castle_time_int'])
        imperial_time = ach(achievements, ['technology', 'imperial_time_int'])
        name = player.attributes.player_name.decode(encoding)
        out.append({
            'name': name,
            'civilization': player.attributes.civilization,
            'human': header.scenario.game_settings.player_info[i + 1].type == 'human',
            'number': i + 1,
            'color_id': player.attributes.player_color,
            'winner': winner,
            'mvp': ach(achievements, ['mvp']),
            'score': ach(achievements, ['total_score']),
            'position': (player.attributes.camera_x, player.attributes.camera_y),
            'rate_snapshot': ratings.get(name),
            'user_id': profile_ids.get(player.attributes.player_color),
            'cheater': (i + 1) in cheaters,
            'achievements': {
                'military': {
                    'score': ach(achievements, ['military', 'score']),
                    'units_killed': ach(achievements, ['military', 'units_killed']),
                    'hit_points_killed': ach(achievements, ['military', 'hit_points_killed']),
                    'units_lost': ach(achievements, ['military', 'units_lost']),
                    'buildings_razed': ach(achievements, ['military', 'buildings_razed']),
                    'hit_points_razed': ach(achievements, ['military', 'hit_points_razed']),
                    'buildings_lost': ach(achievements, ['military', 'buildings_lost']),
                    'units_converted': ach(achievements, ['military', 'units_converted'])
                },
                'economy': {
                    'score': ach(achievements, ['economy', 'score']),
                    'food_collected': ach(achievements, ['economy', 'food_collected']),
                    'wood_collected': ach(achievements, ['economy', 'wood_collected']),
                    'stone_collected': ach(achievements, ['economy', 'stone_collected']),
                    'gold_collected': ach(achievements, ['economy', 'gold_collected']),
                    'tribute_sent': ach(achievements, ['economy', 'tribute_sent']),
                    'tribute_received': ach(achievements, ['economy', 'tribute_received']),
                    'trade_gold': ach(achievements, ['economy', 'trade_gold']),
                    'relic_gold': ach(achievements, ['economy', 'relic_gold'])
                },
                'technology': {
                    'score': ach(achievements, ['technology', 'score']),
                    'feudal_time': feudal_time if feudal_time and feudal_time > 0 else None,
                    'castle_time': castle_time if castle_time and castle_time > 0 else None,
                    'imperial_time': imperial_time if imperial_time and imperial_time > 0 else None,
                    'explored_percent': ach(achievements, ['technology', 'explored_percent']),
                    'research_count': ach(achievements, ['technology', 'research_count']),
                    'research_percent': ach(achievements, ['technology', 'research_percent'])
                },
                'society': {
                    'score': ach(achievements, ['society', 'score']),
                    'total_wonders': ach(achievements, ['society', 'total_wonders']),
                    'total_castles': ach(achievements, ['society', 'total_castles']),
                    'total_relics': ach(achievements, ['society', 'relics_captured']),
                    'villager_high': ach(achievements, ['society', 'villager_high'])
                }
            }
        })
    return out
