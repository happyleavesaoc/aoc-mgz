"""Determine dataset."""

import mgz
from mgz.util import Version
from mgz.reference import get_dataset


def get_dataset_data(header):
    """Get dataset."""
    sample = header.initial.players[0].attributes.player_stats
    mod = None
    if 'mod' in sample:
        mod = (sample.mod.get('id'), sample.mod.get('version'))
    _, ref = get_dataset(header.version, mod)
    if header.version == Version.DE:
        return {
            'id': 100,
            'name': 'Definitive Edition',
            'version': None
        }, ref
    if 'mod' in sample and sample.mod['id'] == 0 and sample.mod['version'] == '2':
        raise ValueError("invalid mod version")
    if 'mod' in sample and sample.mod['id'] > 0:
        return sample.mod, ref
    if 'trickle_food' in sample and sample.trickle_food:
        return {
            'id': 1,
            'name': mgz.const.MODS.get(1),
            'version': '<5.7.2'
        }, ref
    if header.version == Version.AOK:
        return {
            'id': 200,
            'name': 'Age of Kings',
            'version': '2.0a'
        }, ref
    if header.version == Version.AOC10:
        return {
            'id': 0,
            'name': 'The Conquerors',
            'version': '1.0'
        }, ref
    return {
        'id': 0,
        'name': 'The Conquerors',
        'version': '1.0c'
    }, ref
