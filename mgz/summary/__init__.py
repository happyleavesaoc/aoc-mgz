"""MGZ Summary."""

import asyncio
import hashlib
import logging
import os
import struct
import tempfile
import time
import zlib

import construct

import mgz
import mgz.body
from mgz import fast

from mgz.summary.map import get_map_data
from mgz.summary.settings import get_settings_data
from mgz.summary.dataset import get_dataset_data
from mgz.summary.teams import get_teams_data
from mgz.summary.players import get_players_data
from mgz.summary.diplomacy import get_diplomacy_data


LOGGER = logging.getLogger(__name__)
CHECKSUMS = 4
MAX_SYNCS = 2000


class Summary: # pylint: disable=too-many-public-methods
    """MGZ summary.

    Access match summary data.
    """

    def __init__(self, handle, playback=None):
        """Initialize."""
        self.size = len(handle.read())
        handle.seek(0)
        self._handle = handle
        self._playback = playback
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
            'lobby_name': None,
            'duration': None
        }

        try:
            start = time.time()
            self._header = mgz.header.parse_stream(self._handle)
            LOGGER.info("parsed header in %.2f seconds", time.time() - start)
            body_pos = self._handle.tell()
            self._cache['file_hash'] = hashlib.sha1(self._handle.read()).hexdigest()
            self._handle.seek(body_pos)
            self._process_body()
            self.body_pos = body_pos
        except (construct.core.ConstructError, zlib.error, ValueError):
            raise RuntimeError("invalid mgz file")

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
        while True:
            try:
                operation, payload = fast.operation(self._handle)
                if operation == fast.Operation.SYNC:
                    i += 1
                    duration += payload[0]
                    if payload[1] and len(checksums) < CHECKSUMS:
                        checksums.append(payload[1].to_bytes(8, 'big', signed=True))
                elif operation == fast.Operation.ACTION and payload[0] == 255:
                    self._cache['postgame'] = mgz.body.actions.postgame.parse(payload[1]['bytes'])
                elif operation == fast.Operation.ACTION and payload[0] == 11:
                    self._cache['resigned'].add(payload[1]['player_id'])
                elif operation == fast.Operation.CHAT:
                    text = payload
                    if text is None:
                        continue
                    text = text.strip(b'\x00')
                    try:
                        text = text.decode(self.get_encoding())
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
                    except UnicodeDecodeError:
                        pass
            except EOFError:
                break
        self._cache['duration'] = duration
        if voobly:
            rated = ratings and set(ratings.values()) != {1600}
        if self._header.de:
            self._cache['hash'] = hashlib.sha1(self._header.de.guid)
        else:
            self._cache['hash'] = hashlib.sha1(b''.join(checksums)) \
                if len(checksums) == CHECKSUMS else None
        self._cache['from_voobly'] = voobly
        if voobly:
            self._cache['platform_id'] = 'voobly'
        if self._header.de and self._header.de.multiplayer:
            self._cache['platform_id'] = 'de'
        self._cache['ladder'] = ladder
        self._cache['rated'] = rated
        self._cache['ratings'] = ratings if rated else {}
        LOGGER.info("parsed body in %.2f seconds", time.time() - start_time)

    def get_postgame(self):
        """Get postgame structure."""
        return self._cache['postgame']

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
        return mgz.const.VERSIONS[self._header.version], str(self._header.sub_version)[:5]

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
        """Get map of player color to profile IDs (DE only)."""
        if self._header.de is not None:
            return {
                p.color_id: p.profile_id.decode('ascii')
                for p in self._header.de.players
                if p.color_id >= 0
            }
        return {}

    def get_players(self):
        """Get players."""
        return get_players_data(
            self.get_header(),
            self.get_postgame(),
            self.get_teams(),
            self._cache['resigned'],
            self.get_profile_ids(),
            self.get_ratings(),
            self.get_encoding()
        )

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
            lobby_name = self._header.de.lobby_name.decode(self.get_encoding()).strip()
            guid = self._header.de.guid.hex()
            guid_formatted = '{}-{}-{}-{}-{}'.format(
                guid[0:8], guid[8:12], guid[12:16], guid[16:20], guid[20:]
            )
        return {
            'platform_id': self._cache['platform_id'],
            'platform_match_id': guid_formatted,
            'ladder': self._cache['ladder'],
            'rated': self._cache['rated'],
            'ratings': self._cache['ratings'],
            'lobby_name': lobby_name
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

    def get_map(self):
        """Get map."""
        if not self._cache['map']:
            self._cache['map'], self._cache['encoding'], self._cache['language'] = get_map_data(
                self._header.scenario.game_settings.map_id,
                self._header.scenario.messages.instructions,
                self._header.map_info.size_x,
                self._header.de is not None,
                self._header.map_info.tile
            )
        return self._cache['map']

    def get_dataset(self):
        """Get dataset."""
        return get_dataset_data(self._header)

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
        if self.get_diplomacy()['1v1']:
            civs = set()
            for data in self.get_players():
                civs.add(data['civilization'])
            mirror = (len(civs) == 1)
        return mirror

    async def async_extract(self):
        """Full extraction."""
        if self.get_dataset()['id'] != 1:
            raise RuntimeError('extraction not supported')
        if not self._playback:
            raise RuntimeError('no playback host defined')

        from mgz.summary.extract import get_extracted_data

        temp = tempfile.NamedTemporaryFile()
        self._handle.seek(0)
        temp.write(self._handle.read())

        return await get_extracted_data(
            self._header,
            self.get_encoding(),
            self.get_diplomacy().get('type'),
            self.get_players(),
            self.get_start_time(),
            self.get_duration(),
            self._playback,
            temp
        )

    def extract(self):
        """Async wrapper around full extraction."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_extract())
