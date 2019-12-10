"""MGZ Summary."""

import hashlib
import logging
import os
import re
import struct
import tempfile
import time
import zlib

import construct

import mgz
import mgz.body


LOGGER = logging.getLogger(__name__)
SEARCH_MAX_BYTES = 3000
POSTGAME_LENGTH = 2096
LOOKAHEAD = 9
CHECKSUMS = 4
MAX_SYNCS = 2000
ENCODING_MARKERS = [
    ['Map Type: ', 'latin-1', 'en'],
    ['Map type: ', 'latin-1', 'en'],
    ['Location: ', 'latin-1', 'en'],
    ['Tipo de mapa: ', 'latin-1', 'es'],
    ['Ubicaci', 'latin-1', 'es'],
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
    ['颌玉拙墁：', 'cp936', 'zh']
]
LANGUAGE_MARKERS = [
    ['Dostepne', 'ISO-8859-2', 'pl'],
    ['oszukiwania', 'ISO-8859-2', 'pl'],
    ['Dozwoli', 'ISO-8859-2', 'pl'],
    ['Povol', 'ISO-8859-2', 'cs'], # Povolené, Povolit
    ['Mozno', 'ISO-8859-2', 'sk']
]


def find_postgame(data, size):
    """Find postgame struct.

    We can find postgame location by scanning the last few
    thousand bytes of the rec and looking for a pattern as
    follows:

    [action op]    [action length]    [action type]
    01 00 00 00    30 08 00 00        ff

    The last occurance of this pattern signals the start of
    the postgame structure. Note that the postgame action length
    is always constant, unlike other actions.
    """
    pos = None
    for i in range(size - SEARCH_MAX_BYTES, size - LOOKAHEAD):
        op_type, length, action_type = struct.unpack('<IIB', data[i:i + LOOKAHEAD])
        if op_type == 0x01 and length == POSTGAME_LENGTH and action_type == 0xFF:
            LOGGER.debug("found postgame candidate @ %d with length %d", i + LOOKAHEAD, length)
            return i + LOOKAHEAD, length


def parse_postgame(handle, size):
    """Parse postgame structure."""
    data = handle.read()
    postgame = find_postgame(data, size)
    if postgame:
        pos, length = postgame
        try:
            return mgz.body.actions.postgame.parse(data[pos:pos + length])
        except construct.core.ConstructError:
            raise IOError("failed to parse postgame")
    raise IOError("could not find postgame")


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


class Summary:
    """MGZ summary.

    Access metadata that in most cases can be found quickly.
    """

    def __init__(self, handle, size, socket, dropbox):
        """Initialize."""
        self._handle = handle
        self.size = size
        self.socket = socket
        self.dropbox = dropbox
        header_len, = struct.unpack('<I', self._handle.read(4))
        self.body_position = header_len
        self._handle.seek(0)
        self._cache = {
            'teams': None,
            'resigned': set(),
            'encoding': None,
            'language': None,
            'ratings': {},
            'postgame': None,
            'from_voobly': False,
            'platform_id': None,
            'platform_match_id': None,
            'rated': None,
            'ladder': None,
            'hash': None,
            'map': None,
            'lobby_name': None
        }

    def work(self):
        try:
            start = time.time()
            self._header = mgz.header.parse_stream(self._handle)
            LOGGER.info("parsed rec header in %.2f seconds", time.time() - start)
            self._process_body()
        except (construct.core.ConstructError, zlib.error, ValueError):
            raise RuntimeError("invalid mgz file")

    def get_postgame(self):
        """Get postgame structure."""
        if self._cache['postgame'] is not None:
            return self._cache['postgame']
        self._handle.seek(0)
        try:
            self._cache['postgame'] = parse_postgame(self._handle, self.size)
            return self._cache['postgame']
        except IOError:
            self._cache['postgame'] = False
            return None
        finally:
            self._handle.seek(self.body_position)

    def get_header(self):
        return self._header

    def get_start_time(self):
        return self._header.initial.restore_time

    def get_duration(self):
        """Get game duration."""
        postgame = self.get_postgame()
        if postgame:
            return postgame.duration_int * 1000
        duration = self._header.initial.restore_time
        try:
            while self._handle.tell() < self.size:
                operation = mgz.body.operation.parse_stream(self._handle)
                if operation.type == 'sync':
                    duration += operation.time_increment
                elif operation.type == 'action':
                    if operation.action.type == 'resign':
                        self._cache['resigned'].add(operation.action.player_id)
            self._handle.seek(self.body_position)
        except (construct.core.ConstructError, zlib.error, ValueError):
            raise RuntimeError("invalid mgz file")
        return duration

    def get_restored(self):
        """Check for restored game."""
        return self._header.initial.restore_time > 0, self._header.initial.restore_time

    def get_version(self):
        """Get game version."""
        return mgz.const.VERSIONS[self._header.version], str(self._header.sub_version)[:5]

    def get_dataset(self):
        """Get dataset."""
        if self._header.version == 'VER 9.4':
            return {
                'id': 100,
                'name': 'Age of Empires II: Definitive Edition',
                'version': self._header.version[4:]
            }
        sample = self._header.initial.players[0].attributes.player_stats
        if 'mod' in sample and sample.mod['id'] == 0 and sample.mod['version'] == '2':
            raise ValueError("invalid mod version")
        if 'mod' in sample and sample.mod['id'] > 0:
            return sample.mod
        elif 'trickle_food' in sample and sample.trickle_food:
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

    def get_owner(self):
        """Get rec owner (POV)."""
        return self._header.replay.rec_player

    def get_teams(self):
        """Get teams."""
        if self._cache['teams']:
            return self._cache['teams']
        teams = []
        for j, player in enumerate(self._header.initial.players):
            added = False
            for i in range(0, len(self._header.initial.players)):
                if player.attributes.my_diplomacy[i] == 'ally':
                    inner_team = False
                    outer_team = False
                    new_team = True
                    for t, tl in enumerate(teams):
                        if j in tl or i in tl:
                            new_team = False
                        if j in tl and i not in tl:
                            inner_team = t
                            break
                        if j not in tl and i in tl:
                            outer_team = t
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
        self._cache['teams'] = teams
        return teams

    def get_diplomacy(self):
        """Compute diplomacy."""
        if not self._cache['teams']:
            self.get_teams()

        player_num = 0
        computer_num = 0
        for player in self._header.scenario.game_settings.player_info:
            if player.type == 'human':
                player_num += 1
            elif player.type == 'computer':
                computer_num += 1
        total_num = player_num + computer_num

        diplomacy = {
            'FFA': (len(self._cache['teams']) == total_num) and total_num > 2,
            'TG':  len(self._cache['teams']) == 2 and total_num > 2,
            '1v1': total_num == 2,
        }

        diplomacy['type'] = 'Other'
        team_sizes = sorted([len(team) for team in self._cache['teams']])
        diplomacy['team_size'] = 'v'.join([str(size) for size in team_sizes])
        if diplomacy['FFA']:
            diplomacy['type'] = 'FFA'
            diplomacy['team_size'] = 'FFA'
        elif diplomacy['TG']:
            diplomacy['type'] = 'TG'
        elif diplomacy['1v1']:
            diplomacy['type'] = '1v1'
        return diplomacy

    def get_achievements(self, name):
        """Get achievements for a player.

        Must match on name, not index, since order is not always the same.
        """
        postgame = self.get_postgame()
        if not postgame:
            return None
        for achievements in postgame.achievements:
            # achievements player name can be shorter
            if name.startswith(achievements.player_name.replace(b'\x00', b'')):
                return achievements
        return None

    def get_profile_ids(self):
        """Get map of player color to profile IDs (DE only)."""
        if self._header.de is not None:
            return {p.color_id: p.profile_id.decode('ascii') for p in self._header.de.players if p.color_id >= 0}
        return {}

    def get_players(self):
        """Get basic player info."""
        profile_ids = self.get_profile_ids()
        ratings = self.get_ratings()
        for i, player in enumerate(self._header.initial.players[1:]):
            achievements = self.get_achievements(player.attributes.player_name)
            if achievements:
                winner = achievements.victory
            else:
                winner = self.guess_winner(i + 1)
            feudal_time = ach(achievements, ['technology', 'feudal_time_int'])
            castle_time = ach(achievements, ['technology', 'castle_time_int'])
            imperial_time = ach(achievements, ['technology', 'imperial_time_int'])
            name = player.attributes.player_name.decode(self.get_encoding())
            yield {
                'name': name,
                'civilization': player.attributes.civilization,
                'human': self._header.scenario.game_settings.player_info[i + 1].type == 'human',
                'number': i + 1,
                'color_id': player.attributes.player_color,
                'winner': winner,
                'mvp': ach(achievements, ['mvp']),
                'score': ach(achievements, ['total_score']),
                'position': (player.attributes.camera_x, player.attributes.camera_y),
                'rate_snapshot': ratings.get(name),
                'user_id': profile_ids.get(player.attributes.player_color),
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
            }

    def get_ratings(self):
        """Get player ratings."""
        if not self._cache['ratings']:
            self.get_platform()
        return self._cache['ratings']

    def get_platform(self):
        """Get platform data."""
        lobby_name = None
        guid_formatted = None
        if self._header.de is not None:
            lobby_name = self._header.de.lobby_name.decode(self.get_encoding())
            guid = self._header.de.guid.hex()
            guid_formatted = '{}-{}-{}-{}-{}'.format(guid[0:8], guid[8:12], guid[12:16], guid[16:20], guid[20:])
        return {
            'platform_id': self._cache['platform_id'],
            'platform_match_id': guid_formatted,
            'ladder': self._cache['ladder'],
            'rated': self._cache['rated'],
            'ratings': self._cache['ratings'],
            'lobby_name': lobby_name if lobby_name and len(lobby_name) > 0 else None
        }

    def _process_body(self):
        """Get Voobly ladder.

        This is expensive if the rec is not from Voobly,
        since it will search the whole file. Sets cache.
        """
        start_time = time.time()
        ratings = {}
        encoding = self.get_encoding()
        checksums = []
        ladder= None
        voobly = False
        rated = None
        i = 0
        while self._handle.tell() < self.size:
            try:
                op = mgz.body.operation.parse_stream(self._handle)
                if op.type == 'sync':
                    i += 1
                if op.type == 'sync' and op.checksum is not None and len(checksums) < CHECKSUMS:
                    checksums.append(op.checksum.sync.to_bytes(8, 'big', signed=True))
                elif op.type == 'message' and op.subtype == 'chat':
                    text = op.data.text.decode(encoding)
                    if text.find('Voobly: Ratings provided') > 0:
                        start = text.find("'") + 1
                        end = text.find("'", start)
                        ladder = text[start:end]
                        voobly = True
                    elif text.find('<Rating>') > 0:
                        player_start = text.find('>') + 2
                        player_end = text.find(':', player_start)
                        player = text[player_start:player_end]
                        ratings[player] = int(text[player_end + 2:len(text)])
                    elif text.find('No ratings are available') > 0:
                        voobly = True
                    elif text.find('This match was played at Voobly.com') > 0:
                        voobly = True
                if i > MAX_SYNCS:
                    break
            except (construct.core.ConstructError, ValueError):
                break
        self._handle.seek(self.body_position)
        if voobly:
            rated = len(ratings) > 0 and set(ratings.values()) != {1600}
        if self._header.de:
            self._cache['hash'] = hashlib.sha1(self._header.de.guid)
        else:
            self._cache['hash'] = hashlib.sha1(b''.join(checksums)) if len(checksums) == CHECKSUMS else None
        self._cache['from_voobly'] = voobly
        if voobly:
            self._cache['platform_id'] = 'voobly'
        if self._header.de and self._header.de.multiplayer:
            self._cache['platform_id'] = 'de'
        self._cache['ladder'] = ladder
        self._cache['rated'] = rated
        self._cache['ratings'] = ratings if rated else {}
        LOGGER.info("parsed limited rec body in %.2f seconds", time.time() - start_time)

    def _get_all_techs(self, postgame, de):
        """Get all techs flag."""
        if de is not None:
            return de.all_techs
        if postgame is not None:
            return postgame.all_techs
        return None

    def _get_lock_speed(self, postgame, de):
        """Get lock speed flag."""
        if de is not None:
            return de.lock_speed
        if postgame is not None:
            return postgame.lock_speed
        return None

    def _get_team_together(self, postgame, de):
        """Get team together flag."""
        if de is not None:
            return not de.random_positions
        if postgame is not None:
            return not postgame.random_positions
        return None

    def _get_victory_type(self, postgame, de):
        """Get victory type."""
        if de is not None:
            return (de.victory_type_id, de.victory_type)
        if postgame is not None:
            return (postgame.victory_type_id, postgame.victory_type)
        return None

    def _get_starting_resources(self, postgame, de):
        """Get starting resources."""
        if de is not None:
            return (de.starting_resources_id, de.starting_resources)
        if postgame is not None:
            return (postgame.starting_resources_id, postgame.starting_resources)
        return None

    def _get_starting_age(self, postgame, de):
        """Get starting age."""
        if de is not None:
            return (de.starting_age_id, de.starting_age)
        if postgame is not None:
            return (postgame.starting_age_id, postgame.starting_age)
        return None

    def get_settings(self):
        """Get settings."""
        postgame = self.get_postgame()
        population_limit = self._header.lobby.population_limit
        if self._header.de is None:
            population_limit *= 25
        game_speed_id = int(self._header.replay.game_speed_float * 100)
        return {
            'type': (
                self._header.lobby.game_type_id,
                self._header.lobby.game_type
            ),
            'difficulty': (
                self._header.scenario.game_settings.difficulty_id,
                self._header.scenario.game_settings.difficulty
            ),
            'population_limit': population_limit,
            'map_reveal_choice': (
                self._header.lobby.reveal_map_id,
                self._header.lobby.reveal_map
            ),
            'speed': (
                game_speed_id,
                mgz.const.SPEEDS.get(game_speed_id)
            ),
            'starting_resources': self._get_starting_resources(postgame, self._header.de),
            'starting_age': self._get_starting_age(postgame, self._header.de),
            'ending_age': (
                self._header.de.ending_age_id,
                self._header.de.ending_age
            ) if self._header.de else (None, None),
            'victory_condition': self._get_victory_type(postgame, self._header.de),
            'treaty_length': self._header.de.treaty_length if self._header.de else None,
            'cheats': self._header.replay.cheats_enabled,
            'team_together': self._get_team_together(postgame, self._header.de),
            'all_technologies': self._get_all_techs(postgame, self._header.de),
            'lock_speed': self._get_lock_speed(postgame, self._header.de),
            'lock_teams': self._header.lobby.lock_teams,
            'multiqueue': True if self._header.de is not None else None,
        }

    def get_hash(self):
        """Get cached hash."""
        return self._cache['hash']

    def get_encoding(self):
        """Get text encoding."""
        if not self._cache['encoding']:
            self.get_map()
        return self._cache['encoding']

    def get_language(self):
        """Get language."""
        if not self._cache['language']:
            self.get_map()
        return self._cache['language']

    def get_map(self):
        """Get the map metadata."""
        if self._cache['map']:
            return self._cache['map']
        map_id = self._header.scenario.game_settings.map_id
        instructions = self._header.scenario.messages.instructions
        size = mgz.const.MAP_SIZES.get(self._header.map_info.size_x)
        dimension = self._header.map_info.size_x
        if dimension == 255:
            raise ValueError('invalid map size')
        custom = True
        name = 'Unknown'
        language = None
        encoding = 'unknown'
        if instructions == b'\x00':
            raise ValueError('empty instructions')

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
        self._cache['encoding'] = encoding
        self._cache['language'] = language

        # lookup base game map if applicable
        if (map_id != 44 and not self._header.de) or (map_id != 59 and self._header.de):
            if map_id not in mgz.const.MAP_NAMES:
                raise ValueError('unspecified builtin map')
            name = mgz.const.MAP_NAMES[map_id]
            custom = False

        # extract map seed
        match = re.search(b'\x00.*? (\-?[0-9]+)\x00.*?\.rms', instructions)
        seed = None
        if match:
            seed = int(match.group(1))

        # extract userpatch modes
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

        self._cache['map'] = {
            'id': map_id if not custom else None,
            'name': name.strip(),
            'size': size,
            'dimension': dimension,
            'seed': seed,
            'modes': modes,
            'custom': custom,
            'zr': name.startswith('ZR@')
        }
        return self._cache['map']

    def get_completed(self):
        """Determine if the game was completed.

        If there's a postgame, it will indicate completion.
        If there is no postgame, guess based on resignation.
        """
        postgame = self.get_postgame()
        if postgame:
            return postgame.complete
        else:
            return True if self._cache['resigned'] else False

    def get_mirror(self):
        """Determine mirror match."""
        mirror = False
        if self.get_diplomacy()['1v1']:
            civs = set()
            for data in self.get_players():
                civs.add(data['civilization'])
            mirror = (len(civs) == 1)
        return mirror

    def guess_winner(self, i):
        """Guess if a player won.

        Find what team the player was on. If anyone
        on their team resigned, assume the player lost.
        """
        for team in self.get_teams():
            if i not in team:
                continue
            for p in team:
                if p in self._cache['resigned']:
                    return False
        return True
