"""Determine dataset."""

import mgz


def get_dataset_data(header):
    """Get dataset."""
    if header.version == 'VER 9.4':
        return {
            'id': 100,
            'name': 'Age of Empires II: Definitive Edition',
            'version': header.version[4:]
        }
    sample = header.initial.players[0].attributes.player_stats
    if 'mod' in sample and sample.mod['id'] == 0 and sample.mod['version'] == '2':
        raise ValueError("invalid mod version")
    if 'mod' in sample and sample.mod['id'] > 0:
        return sample.mod
    if 'trickle_food' in sample and sample.trickle_food:
        return {
            'id': 1,
            'name': mgz.const.MODS.get(1),
            'version': '<5.7.2'
        }
    return {
        'id': 0,
        'name': 'Age of Kings: The Conquerors',
        'version': '1.0c'
    }
