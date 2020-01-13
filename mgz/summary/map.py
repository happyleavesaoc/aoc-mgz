"""Map summary."""

import re
import mgz


ENCODING_MARKERS = [
    ['Map Type: ', 'latin-1', 'en'],
    ['Map type: ', 'latin-1', 'en'],
    ['Location: ', 'utf-8', 'en'],
    ['Tipo de mapa: ', 'latin-1', 'es'],
    ['Ubicación: ', 'utf-8', 'es'],
    ['Ubicaci: ', 'utf-8', 'es'],
    ['Kartentyp: ', 'latin-1', 'de'],
    ['Art der Karte: ', 'latin-1', 'de'],
    ['Type de carte\xa0: ', 'latin-1', 'fr'],
    ['Type de carte : ', 'latin-1', 'fr'],
    ['Tipo di mappa: ', 'latin-1', 'it'],
    ['Tipo de Mapa: ', 'latin-1', 'pt'],
    ['Kaarttype', 'latin-1', 'nl'],
    ['Harita Türü: ', 'ISO-8859-1', 'tr'],
    ['Harita Sitili', 'ISO-8859-1', 'tr'],
    ['Harita tipi', 'ISO-8859-1', 'tr'],
    ['??? ?????: ', 'ascii', 'tr'], # corrupt lang dll?
    ['Térkép tipusa', 'ISO-8859-1', 'hu'],
    ['Typ mapy: ', 'ISO-8859-2', None],
    ['Тип карты: ', 'windows-1251', 'ru'],
    ['Тип Карты: ', 'windows-1251', 'ru'],
    ['マップの種類: ', 'SHIFT_JIS', 'jp'],
    ['지도 종류: ', 'cp949', 'kr'],
    ['地??型', 'big5', 'zh'],
    ['地图类型: ', 'cp936', 'zh'],
    ['地圖類別：', 'cp936', 'zh'],
    ['地圖類別：', 'big5', 'zh'],
    ['地图类别：', 'cp936', 'zh'],
    ['地图类型：', 'GB2312', 'zh'],
    ['颌玉拙墁：', 'cp936', 'zh'],
    ['位置：', 'utf-8', 'zh']
]
LANGUAGE_MARKERS = [
    ['Dostepne', 'ISO-8859-2', 'pl'],
    ['oszukiwania', 'ISO-8859-2', 'pl'],
    ['Dozwoli', 'ISO-8859-2', 'pl'],
    ['Povol', 'ISO-8859-2', 'cs'], # Povolené, Povolit
    ['Mozno', 'ISO-8859-2', 'sk'],
    ['Dobývací', 'ISO-8859-2', 'cs']
]


def extract_from_instructions(instructions):
    """Extract data from instructions."""
    language = None
    encoding = 'unknown'
    name = 'Unknown'
    for pair in ENCODING_MARKERS:
        marker = pair[0]
        test_encoding = pair[1]
        e_m = marker.encode(test_encoding)
        for line in instructions.split(b'\n'):
            pos = line.find(e_m)
            if pos > -1:
                encoding = test_encoding
                name = line[pos+len(e_m):].decode(encoding).replace('.rms', '')
                language = pair[2]
                break

    # disambiguate certain languages
    if not language:
        language = 'unknown'
        for pair in LANGUAGE_MARKERS:
            if instructions.find(pair[0].encode(pair[1])) > -1:
                language = pair[2]
                break
    return encoding, language, name


def lookup_name(map_id, name, is_de):
    """Lookup base game map if applicable."""
    custom = True
    if (map_id != 44 and not is_de) or (map_id != 59 and is_de):
        if is_de and map_id in mgz.const.DE_MAP_NAMES:
            name = mgz.const.DE_MAP_NAMES[map_id]
        elif not is_de and map_id in mgz.const.MAP_NAMES:
            name = mgz.const.MAP_NAMES[map_id]
        else:
            raise ValueError('unspecified builtin map: ' + str(map_id))
        custom = False
    return name, custom


def get_map_seed(instructions):
    """Extract map seed from instructions."""
    match = re.search(rb'\x00.*? (\-?[0-9]+)\x00.*?\.rms', instructions)
    seed = None
    if match:
        seed = int(match.group(1))
    return seed


def get_modes(name):
    """Extract userpatch modes."""
    has_modes = name.find(': !')
    mode_string = ''
    if has_modes > -1:
        mode_string = name[has_modes + 3:]
        name = name[:has_modes]
    modes = {
        'direct_placement': 'P' in mode_string,
        'effect_quantity': 'C' in mode_string,
        'guard_state': 'G' in mode_string,
        'fixed_positions': 'F' in mode_string
    }
    return name, modes


def get_tiles(tiles, dimension):
    """Get map tile data."""
    tile_x = 0
    tile_y = 0
    for tile in tiles:
        if tile_x == dimension:
            tile_x = 0
            tile_y += 1
        yield {
            'x': tile_x,
            'y': tile_y,
            'terrain_id': tile.terrain_type,
            'elevation': tile.elevation
        }
        tile_x += 1


def get_map_data(map_id, instructions, dimension, is_de, tiles):
    """Get the map metadata."""
    if dimension == 255:
        raise ValueError('invalid map size')
    if instructions == b'\x00':
        raise ValueError('empty instructions')

    encoding, language, name = extract_from_instructions(instructions)
    name, custom = lookup_name(map_id, name, is_de)
    seed = get_map_seed(instructions)
    name, modes = get_modes(name)

    return {
        'id': map_id if not custom else None,
        'name': name.strip(),
        'size': mgz.const.MAP_SIZES.get(dimension),
        'dimension': dimension,
        'seed': seed,
        'modes': modes,
        'custom': custom,
        'zr': name.startswith('ZR@'),
        'tiles': list(get_tiles(tiles, dimension))
    }, encoding, language
