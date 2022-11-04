"""Map summary."""

import re
import mgz
from mgz.util import Version


ENCODING_MARKERS = [
    ['Map Type: ', 'latin-1', 'en'],
    ['Map type: ', 'latin-1', 'en'],
    ['Location: ', 'utf-8', 'en'],
    ['Tipo de mapa: ', 'latin-1', 'es'],
    ['Ubicación: ', 'utf-8', 'es'],
    ['Ubicaci: ', 'utf-8', 'es'],
    ['Local: ', 'utf-8', 'es'],
    ['Kartentyp: ', 'latin-1', 'de'],
    ['Karte: ', 'utf-8', 'de'],
    ['Art der Karte: ', 'latin-1', 'de'],
    ['Type de carte\xa0: ', 'latin-1', 'fr'],
    ['Emplacement :', 'utf-8', 'fr'],
    ['Type de carte : ', 'latin-1', 'fr'],
    ['Tipo di mappa: ', 'latin-1', 'it'],
    ['Posizione: ', 'utf-8', 'it'],
    ['Tipo de Mapa: ', 'latin-1', 'pt'],
    ['Kaarttype', 'latin-1', 'nl'],
    ['Lokalizacja: ', 'utf-8', 'pl'],
    ['Harita Türü: ', 'ISO-8859-1', 'tr'],
    ['Harita Sitili', 'ISO-8859-1', 'tr'],
    ['Harita tipi', 'ISO-8859-1', 'tr'],
    ['Konum: ', 'ISO-8859-1', 'tr'],
    ['??? ?????: ', 'ascii', 'tr'], # corrupt lang dll?
    ['Térkép tipusa', 'ISO-8859-1', 'hu'],
    ['Typ mapy: ', 'ISO-8859-2', None],
    ['Тип карты: ', 'windows-1251', 'ru'],
    ['Тип Карты: ', 'windows-1251', 'ru'],
    ['Расположение: ', 'utf-8', 'ru'],
    ['マップの種類: ', 'SHIFT_JIS', 'jp'],
    ['マップ ', 'utf-8', 'jp'],
    ['지도 종류: ', 'cp949', 'kr'],
    ['地??型', 'big5', 'zh'],
    ['地图类型: ', 'cp936', 'zh'],
    ['地圖類別：', 'cp936', 'zh'],
    ['地圖類別：', 'big5', 'zh'],
    ['地图类别：', 'cp936', 'zh'],
    ['地图类型：', 'GB2312', 'zh'],
    ['颌玉拙墁：', 'cp936', 'zh'],
    ['位置：', 'utf-8', 'zh'],
    ['舞台: ', 'utf-8', 'zh'],
    ['Vị trí: ', 'utf-8', 'vi'],
    ['위치: ', 'utf-8', 'kr'],
    ['Τύπος Χάρτη: ', 'utf-8', 'gr'],
    ['Emplacement: ', 'utf-8', 'fr'],
    ['Local: ', 'utf-8', 'pt'],
    ['Mapa: ', 'utf-8', 'cs'],
    ['Plats: ', 'utf-8', 'se']
]
LANGUAGE_MARKERS = [
    ['Dostepne', 'ISO-8859-2', 'pl'],
    ['oszukiwania', 'ISO-8859-2', 'pl'],
    ['Dozwoli', 'ISO-8859-2', 'pl'],
    ['Povol', 'ISO-8859-2', 'cs'], # Povolené, Povolit
    ['Mozno', 'ISO-8859-2', 'sk'],
    ['Dobývací', 'ISO-8859-2', 'cs']
]
WATER_TERRAIN = {
    0: [1, 4, 15, 22, 23],
    1: [1, 4, 11, 15, 22, 23],
    7: [1, 4, 15, 22, 23],
    100: [1, 4, 15, 22, 23, 26, 54, 57, 58, 59, 93, 94, 95, 96, 97, 98, 99]
}


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
            has = line.startswith(e_m)
            if has:
                pos = 0
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
    if encoding == 'unknown':
        raise ValueError('could not detect encoding')
    return encoding, language, name


def lookup_name(map_id, name, version, reference):
    """Lookup base game map if applicable."""
    custom = True
    is_de = version == Version.DE
    is_hd = version == Version.HD
    # 59: RM custom
    # 137: custom map pool
    # 138: DM custom
    if (map_id != 44 and not (is_de or is_hd)) or (map_id not in [59, 137, 138] and (is_de or is_hd)):
        map_keys = [int(k) for k in reference['maps'].keys()]
        if map_id in map_keys:
            name = reference['maps'][str(map_id)]
        elif version == Version.AOK:
            return name, False
        else:
            raise ValueError('unspecified builtin map: {} aka {} ({})'.format(map_id, name, reference['dataset']['name']))
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
            'terrain_id': tile[0],
            'elevation': tile[1]
        }
        tile_x += 1


def get_water_percent(tiles, dataset_id):
    """Get percent of map that is passable by ships."""
    if dataset_id not in WATER_TERRAIN:
        return None
    count = 0
    for tile in tiles:
        if tile[0] in WATER_TERRAIN[dataset_id]:
            count +=1
    return count/len(tiles)


def get_mod_id(strings):
    """Extract RMS mod id."""
    for obj in strings:
        if not obj.string:
            continue
        s = obj.string.value.decode('utf-8').split(':')
        if s[0] == 'SUBSCRIBEDMODS' and s[1] == 'RANDOM_MAPS':
            return s[3].split('_')[0]


def get_map_data(map_id, instructions, dimension, version, dataset_id, reference, tiles, de_seed=None, de_strings=[]):
    """Get the map metadata."""
    if instructions == b'\x00':
        raise ValueError('empty instructions')
    
    encoding, language, name = extract_from_instructions(instructions)
    name, custom = lookup_name(map_id, name, version, reference)
    seed = get_map_seed(instructions)
    name, modes = get_modes(name)

    return {
        'id': map_id if not custom else None,
        'name': name.strip(),
        'size': mgz.const.MAP_SIZES.get(dimension),
        'dimension': dimension,
        'seed': de_seed if de_seed else seed,
        'mod_id': get_mod_id(de_strings) if custom else None,
        'modes': modes,
        'custom': custom,
        'zr': name.startswith('ZR@'),
        'tiles': list(get_tiles(tiles, dimension)),
        'water': get_water_percent(tiles, dataset_id)
    }, encoding, language
