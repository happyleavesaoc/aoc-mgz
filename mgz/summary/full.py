"""MGZ Summary."""

import asyncio
import collections
import hashlib
import logging
import os
import io
import json
import struct
import tempfile
import time
import uuid
import zlib

import construct

import mgz
import mgz.body
from mgz import fast
from mgz.util import Version

from mgz.const import VALID_BUILDINGS
from mgz.common.map import get_map_data
from mgz.summary.settings import get_settings_data
from mgz.summary.dataset import get_dataset_data
from mgz.summary.teams import get_teams_data
from mgz.summary.players import get_players_data, enrich_de_player_data
from mgz.common.diplomacy import get_diplomacy_data
from mgz.common.chat import get_lobby_chat, parse_chat, Chat
from mgz.summary.objects import get_objects_data


LOGGER = logging.getLogger(__name__)
CHECKSUMS = 4
MAX_SYNCS = 2000
AI_ACTIONS = [fast.Action.AI_ORDER]


class FullSummary: # pylint: disable=too-many-public-methods
    """MGZ summary.

    Access match summary data.
    """

    def __init__(self, handle):
        """Initialize."""
        self.size = len(handle.read())
        handle.seek(0)
        self._handle = handle
        self._cache = {
            'dataset': None,
            'teams': None,
            'resigned': set(),
            'cheaters': set(),
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
            'lobby_name': None,
            'duration': None,
            'extraction': None
        }
        self._eapm = collections.Counter()

        try:
            start = time.time()
            self._header = mgz.header.parse_stream(self._handle)
            LOGGER.info("parsed header in %.2f seconds", time.time() - start)
            self._chats = get_lobby_chat(
                self._header, self.get_encoding(),
                self.get_diplomacy().get('type'), self.get_players()
            )
            body_pos = self._handle.tell()
            self._cache['file_hash'] = hashlib.sha1(self._handle.read()).hexdigest()
            self._handle.seek(body_pos)
            self._process_body()
            self.body_pos = body_pos
        except (construct.core.ConstructError, zlib.error, ValueError) as e:
            raise RuntimeError("invalid mgz file: {}".format(e))

    def _process_body(self): # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        """Process rec body."""
        start_time = time.time()
        ratings = {}
        checksums = []
        ladder = None
        voobly = False
        rated = None
        i = 0
        duration = self._header.initial.restore_time
        fast.meta(self._handle)
        self._actions = []
        while True:
            try:
                operation, payload = fast.operation(self._handle)
                if operation == fast.Operation.SYNC:
                    i += 1
                    duration += payload[0]
                    if payload[1] and len(checksums) < CHECKSUMS:
                        checksums.append(payload[1].to_bytes(8, 'big', signed=True))
                elif operation == fast.Operation.ACTION:
                    if 'player_id' in payload[1] and payload[0] not in AI_ACTIONS:
                        self._eapm[payload[1]['player_id']] += 1
                    self._actions.append((duration, *payload))
                    if payload[0] == fast.Action.POSTGAME:
                        self._cache['postgame'] = mgz.body.actions.postgame.parse(payload[1]['bytes'])
                    elif payload[0] == fast.Action.RESIGN:
                        self._cache['resigned'].add(payload[1]['player_id'])
                    elif payload[0] == fast.Action.TRIBUTE and 'player_id_to' in payload[1] and payload[1]['player_id_to'] == 0:
                        self._cache['cheaters'].add(payload[1]['player_id'])
                    elif payload[0] == fast.Action.TRIBUTE and payload[1]['player_id'] == 0:
                        self._cache['cheaters'].add(payload[1]['player_id_to'])
                    elif payload[0] == fast.Action.CREATE:
                        self._cache['cheaters'].add(payload[1]['player_id'])
                    elif payload[0] == fast.Action.BUILD and payload[1]['building_id'] not in VALID_BUILDINGS:
                        self._cache['cheaters'].add(payload[1]['player_id'])
                    elif payload[0] == fast.Action.GAME and payload[1]['command_id'] in [2, 4, 6]:
                        self._cache['cheaters'].add(payload[1]['player_id'])
                elif operation == fast.Operation.CHAT:
                    text = payload
                    if text is None:
                        continue
                    try:
                        parsed = parse_chat(
                            text, self.get_encoding(), duration, self.get_players(), self.get_diplomacy().get('type')
                        )
                        self._chats.append(parsed)
                        if parsed['type'] == Chat.RATING:
                            ratings[parsed['player']] = parsed['rating']
                        elif parsed['type'] == Chat.LADDER:
                            ladder = parsed['ladder']
                        elif parsed['type'] == Chat.VOOBLY:
                            voobly = True
                    except UnicodeDecodeError:
                        pass
            except EOFError:
                break
        self._cache['duration'] = duration
        if voobly:
            rated = len(ratings) > 0 and set(ratings.values()) != {1600}
        if self._header.version == Version.DE:
            self._cache['hash'] = hashlib.sha1(self._header.de.guid)
        elif self._header.version == Version.HD and self._header.save_version >= 12.49:
            self._cache['hash'] = hashlib.sha1(self._header.hd.guid)
        else:
            self._cache['hash'] = hashlib.sha1(b''.join(checksums)) \
                if len(checksums) == CHECKSUMS else None
        if self._header.de:
            rated = self._header.de.ranked
        self._cache['from_voobly'] = voobly
        if voobly:
            self._cache['platform_id'] = 'voobly'
        if self._header.version == Version.DE and self._header.de.multiplayer:
            self._cache['platform_id'] = 'de'
        if self._header.version == Version.HD and self._header.hd.multiplayer:
            self._cache['platform_id'] = 'hd'
        self._cache['ladder'] = ladder
        self._cache['rated'] = rated
        self._cache['ratings'] = ratings if rated else {}
        LOGGER.info("parsed body in %.2f seconds", time.time() - start_time)

    def get_chat(self):
        """Get chat messages."""
        return self._chats

    def get_postgame(self):
        """Get postgame structure."""
        return self._cache['postgame']

    def has_achievements(self):
        """If match has achievements available."""
        return self._cache['postgame'] is not None or self._cache['extraction'] is not None

    def get_header(self):
        """Get header."""
        return self._header

    def get_start_time(self):
        """Get match start time delta."""
        return self._header.initial.restore_time

    def get_duration(self):
        """Get game duration."""
        return self._cache['duration']

    def get_restored(self):
        """Check for restored game."""
        return self._header.initial.restore_time > 0, self._header.initial.restore_time

    def get_version(self):
        """Get game version."""
        build = None
        if self._header.de:
            build = self._header.de.build
        return self._header.version, self._header.game_version, self._header.save_version, self._header.log_version, build

    def get_owner(self):
        """Get rec owner (POV)."""
        return self._header.replay.rec_player

    def get_teams(self):
        """Get teams."""
        if not self._cache['teams']:
            self._cache['teams'] = get_teams_data(self._header)
        return self._cache['teams']

    def get_diplomacy(self):
        """Compute diplomacy."""
        return get_diplomacy_data(self.get_header(), self.get_teams())

    def get_profile_ids(self):
        """Get map of player color to profile IDs (DE/HD only)."""
        if self._header.version == Version.DE:
            key = 'de'
            field = 'profile_id'
        elif self._header.version == Version.HD and self._header.save_version >= 12.49:
            key = 'hd'
            field = 'steam_id'
        else:
            return {}
        return {
            p.player_number: p[field]
            for p in self._header[key].players
            if p.player_number >= 0 and p[field] > 0
        }

    def get_players(self):
        """Get players."""
        data = get_players_data(
            self.get_header(),
            self.get_postgame(),
            self.get_teams(),
            self._cache['resigned'],
            self._cache['cheaters'],
            self.get_profile_ids(),
            self.get_ratings(),
            self.get_encoding(),
            {id_:int(round(v/((self.get_duration()/1000)/60))) for id_, v in self._eapm.items() if self.get_duration() and v}
        )
        if self._cache['extraction']:
            enrich_de_player_data(data, self._cache['extraction'])
        return data

    def get_objects(self):
        """Get objects."""
        return get_objects_data(self._header)

    def get_ratings(self):
        """Get player ratings."""
        if not self._cache['ratings']:
            self.get_platform()
        return self._cache['ratings']

    def get_platform(self):
        """Get platform data."""
        lobby_name = None
        guid = None
        if self._header.version == Version.DE:
            lobby_name = self._header.de.lobby_name.value.decode(self.get_encoding()).strip()
            guid = str(uuid.UUID(bytes=self._header.de.guid))
        elif self._header.version == Version.HD and self._header.save_version >= 12.49:
            lobby_name = self._header.hd.lobby_name.value.decode(self.get_encoding()).strip()
            guid = str(uuid.UUID(bytes=self._header.hd.guid))
            rating_key = "hd_{}_rating".format(self._header.lobby.game_type.lower())
            for player in self._header.hd.players:
                if player.player_number < 1:
                    continue
                if rating_key not in player:
                    continue
                self._cache['ratings'][player.name.value.decode(self.get_encoding())] = player[rating_key]
            self._cache['rated'] = self._header.hd.is_ranked
        return {
            'platform_id': self._cache['platform_id'],
            'platform_match_id': guid,
            'ladder': self._cache['ladder'],
            'rated': self._cache['rated'],
            'ratings': self._cache['ratings'],
            'lobby_name': lobby_name,
            'allow_specs': self._header.de.allow_specs if self._header.de else None,
            'spec_delay': self._header.de.spec_delay if self._header.de else None,
            'private': self._header.de.lobby_visibility == 2 if self._header.de else None,
        }

    def get_settings(self):
        """Get settings."""
        return get_settings_data(self.get_postgame(), self._header)

    def get_file_hash(self):
        """Get file hash."""
        return self._cache['file_hash']

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

    def get_map_id(self):
        """Get map ID."""
        if self._header.hd:
            return self._header.hd.selected_map_id
        if self._header.de:
            return self._header.de.resolved_map_id
        return self._header.scenario.game_settings.map_id

    def get_map(self):
        """Get map."""
        tiles = tiles = [(tile.terrain_type, tile.elevation) for tile in self._header.map_info.tile]
        if not self._cache['map']:
            self._cache['map'], self._cache['encoding'], self._cache['language'] = get_map_data(
                self.get_map_id(),
                self._header.scenario.messages.instructions,
                self._header.map_info.size_x,
                self._header.version,
                self.get_dataset()['id'],
                self.reference,
                tiles,
                de_seed=self._header.lobby.de.map_seed if self._header.lobby.de else None,
                de_strings=self._header.de.rms_strings.strings if self._header.de else []
            )
        return self._cache['map']

    def get_dataset(self):
        """Get dataset."""
        if not self._cache['dataset']:
            self._cache['dataset'] = get_dataset_data(self._header)
        self.reference = self._cache['dataset'][1]
        return self._cache['dataset'][0]

    def get_completed(self):
        """Determine if the game was completed.

        If there's a postgame, it will indicate completion.
        If there is no postgame, guess based on resignation.
        """
        postgame = self.get_postgame()
        if postgame:
            return postgame.complete
        return bool(self._cache['resigned'])

    def get_mirror(self):
        """Determine mirror match."""
        mirror = False
        if self.get_diplomacy()['type'] == '1v1':
            civs = set()
            for data in self.get_players():
                civs.add(data['civilization'])
            mirror = (len(civs) == 1)
        return mirror

    def get_played(self):
        if self._header.de:
            return self._header.de.timestamp
