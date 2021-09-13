"""Determine dataset."""

import mgz
from mgz.util import Version
from mgz.reference import get_dataset


def resolve_hd_version(hd, save_version):
    """Best guess at HD version."""
    if hd.version == 1006:
        if 'test_57' in hd and hd.test_57.is_57:
            return '5.7'
        else:
            return '5.8'
    if hd.version == 1005:
        return '>=5.0,<5.7'
    if hd.version == 1004:
        return '4.8'
    if save_version >= 12.36:
        return '>=4.6,<4.8'
    return None


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
    elif header.version == Version.HD:
        return {
            'id': 300,
            'name': 'HD Edition',
            'version': resolve_hd_version(header.hd, header.save_version)
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
