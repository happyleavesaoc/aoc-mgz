"""Determine match settings."""


import mgz


def _get_all_techs(postgame, de_data):
    """Get all techs flag."""
    if de_data is not None:
        return de_data.all_techs
    if postgame is not None:
        return postgame.all_techs
    return None


def _get_lock_speed(postgame, de_data):
    """Get lock speed flag."""
    if de_data is not None:
        return de_data.lock_speed
    if postgame is not None:
        return postgame.lock_speed
    return None


def _get_team_together(postgame, de_data):
    """Get team together flag."""
    if de_data is not None:
        return not de_data.random_positions
    if postgame is not None:
        return not postgame.random_positions
    return None


def _get_victory_type(postgame, de_data):
    """Get victory type."""
    if de_data is not None:
        return (de_data.victory_type_id, de_data.victory_type)
    if postgame is not None:
        return (postgame.victory_type_id, postgame.victory_type)
    return (None, None)


def _get_starting_resources(postgame, de_data):
    """Get starting resources."""
    if de_data is not None:
        return (de_data.starting_resources_id, de_data.starting_resources)
    if postgame is not None:
        return (postgame.starting_resources_id, postgame.starting_resources)
    return (None, None)


def _get_starting_age(postgame, de_data):
    """Get starting age."""
    if de_data is not None:
        return (de_data.starting_age_id, de_data.starting_age)
    if postgame is not None:
        return (postgame.starting_age_id, postgame.starting_age)
    return (None, None)


def get_settings_data(postgame, header):
    """Get settings."""
    population_limit = header.lobby.population_limit
    game_speed_id = int(header.replay.game_speed_float * 100)
    return {
        'type': (
            header.lobby.game_type_id,
            header.lobby.game_type
        ) if hasattr(header.lobby, 'game_type_id') else (0, 'RM'),
        'difficulty': (
            header.scenario.game_settings.difficulty_id,
            header.scenario.game_settings.difficulty
        ),
        'population_limit': population_limit,
        'map_reveal_choice': (
            header.lobby.reveal_map_id,
            header.lobby.reveal_map
        ),
        'speed': (
            game_speed_id,
            mgz.const.SPEEDS.get(game_speed_id)
        ),
        'starting_resources': _get_starting_resources(postgame, header.de),
        'starting_age': _get_starting_age(postgame, header.de),
        'ending_age': (
            header.de.ending_age_id,
            header.de.ending_age
        ) if header.de else (None, None),
        'victory_condition': _get_victory_type(postgame, header.de),
        'treaty_length': header.de.treaty_length if header.de else None,
        'cheats': header.replay.cheats_enabled if hasattr(header.replay, 'cheats_enabled') else False,
        'team_together': _get_team_together(postgame, header.de),
        'all_technologies': _get_all_techs(postgame, header.de),
        'lock_speed': _get_lock_speed(postgame, header.de),
        'lock_teams': header.lobby.lock_teams if hasattr(header.replay, 'lock_teams') else True,
        'multiqueue': True if header.de is not None else None,
    }
