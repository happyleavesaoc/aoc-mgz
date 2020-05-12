"""Determine player data."""

from collections import defaultdict


def enrich_de_player_data(players, extraction):
    """Enrich player data with extracted data."""
    last_records = {}
    research_count = defaultdict(int)
    castles = defaultdict(int)
    wonders = defaultdict(int)
    age_times = {}

    for player in players:
        last_records[player['number']] = None
        age_times[player['number']] = {}

    for record in reversed(extraction['timeseries']):
        if not last_records[record['player_number']]:
            last_records[record['player_number']] = record
        if all(last_records.values()):
            break

    for obj in extraction['objects']:
        if obj['initial_object_id'] == 82:
            castles[obj['initial_player_number']] += 1
        elif obj['initial_object_id'] == 276:
            wonders[obj['initial_player_number']] += 1

    for research in extraction['research']:
        if not research['finished']:
            continue
        if research['technology_id'] in [101, 102, 103]:
            age_times[research['player_number']][research['technology_id']] = int(research['started'] / 1000)
        research_count[research['player_number']] += 1

    for player in players:
        record = last_records[player['number']]
        player.update(dict(
            score=record['total_score'],
            winner=player['number'] in extraction['winners']
        ))
        player['achievements']['military'].update(dict(
            score=record['military_score'],
            units_killed=record['kills'],
            units_lost=record['deaths'],
            buildings_lost=record['buildings_lost'],
            buildings_razed=record['razes'],
            units_converted=record['converted'],
            hit_points_killed=record['hit_points_killed'],
            hit_points_razed=record['hit_points_razed']
        ))
        player['achievements']['economy'].update(dict(
            score=record['economy_score'],
            food_collected=record['total_food'],
            wood_collected=record['total_wood'],
            stone_collected=record['total_stone'],
            gold_collected=record['total_gold'],
            tribute_sent=record['tribute_sent'],
            tribute_received=record['tribute_received'],
            trade_gold=record['trade_profit'],
            relic_gold=record['relic_gold']
        ))
        player['achievements']['society'].update(dict(
            score=record['society_score'],
            total_relics=record['relics_captured'],
            total_castles=castles[player['number']],
            total_wonders=wonders[player['number']],
            villager_high=record['villager_high']
        ))
        player['achievements']['technology'].update(dict(
            score=record['technology_score'],
            explored_percent=record['percent_explored'],
            research_count=research_count[player['number']],
            feudal_time=age_times[player['number']].get(101),
            castle_time=age_times[player['number']].get(102),
            imperial_time=age_times[player['number']].get(103)
        ))


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

    If there were no resignations, the game ended
    by some other condition (wonder, timelimit, etc),
    assuming it did complete.
    """
    for team in teams:
        if i not in team:
            continue
        for j in team:
            if j in resigned:
                return False
    if len(resigned) > 0:
        return True
    return None


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
            'user_id': profile_ids.get(i + 1),
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
