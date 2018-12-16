"""MGZ Summary."""

import hashlib
import logging
import os
import struct

import construct
import mgz
import mgz.body


LOGGER = logging.getLogger(__name__)
SEARCH_MAX_BYTES = 3000
POSTGAME_LENGTH = 2096
LOOKAHEAD = 9
CHECKSUMS = 2


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
            LOGGER.debug("found postgame candidate @ %d with length %d", pos, length)
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


class Summary:
    """MGZ summary.

    Access metadata that in most cases can be found quickly.
    """

    def __init__(self, handle, size):
        """Initialize."""
        self._handle = handle
        try:
            self._header = mgz.header.parse_stream(handle)
        except construct.core.ConstructError:
            raise RuntimeError("invalid mgz file")
        self._body_position = self._handle.tell()
        self.size = size

    def get_postgame(self):
        """Get postgame structure."""
        self._handle.seek(0)
        try:
            return parse_postgame(self._handle, self.size)
        except IOError:
            return None
        finally:
            self._handle.seek(self._body_position)

    def get_duration(self):
        """Get game duration."""
        postgame = self.get_postgame()
        if postgame:
            return postgame.duration_int * 1000
        duration = self._header.initial.restore_time
        while self._handle.tell() < self.size:
            operation = mgz.body.operation.parse_stream(self._handle)
            if operation.type == 'sync':
                duration += operation.time_increment
        self._handle.seek(self._body_position)
        return duration

    def get_restored(self):
        """Check for restored game."""
        return self._header.initial.restore_time > 0, self._header.initial.restore_time

    def get_version(self):
        """Get game version."""
        return mgz.const.VERSIONS[self._header.version], str(self._header.sub_version)[:5]

    def get_mod(self):
        """Get mod, if there is one."""
        sample = self._header.initial.players[0].attributes.player_stats
        if 'mod' in sample and sample.mod['id'] > 0:
            return sample.mod['name'], sample.mod['version']
        return None, None

    def get_owner(self):
        """Get rec owner (POV)."""
        return self._header.replay.rec_player

    def get_players(self):
        """Get basic player info."""
        for i, player in enumerate(self._header.initial.players[1:]):
            yield {
                'name': player.attributes.player_name,
                'civilization': player.attributes.civilization,
                'human': self._header.scenario.game_settings.player_info[i + 1].type == 'human',
                'number': i + 1,
                'color_id': player.attributes.player_color
            }

    def get_ladder(self):
        """Get Voobly ladder.

        This is expensive if the rec is not from Voobly,
        since it will search the whole file.
        """
        ladder = None
        while self._handle.tell() < self.size:
            op = mgz.body.operation.parse_stream(self._handle)
            if op.type == 'message' and op.subtype == 'chat':
                if op.data.text.find('Voobly: Ratings provided') > 0:
                    start = op.data.text.find("'") + 1
                    end = op.data.text.find("'", start)
                    ladder = op.data.text[start:end]
                    break
                elif op.data.text.find('No ratings are available') > 0:
                    break
        self._handle.seek(self._body_position)
        return ladder

    def get_hash(self):
        """Compute match hash.

        Use the first three synchronization checksums
        as a unique identifier for the match.
        """
        self._handle.seek(self._body_position)
        checksums = []
        while self._handle.tell() < self.size and len(checksums) < CHECKSUMS:
            op = mgz.body.operation.parse_stream(self._handle)
            if op.type == 'sync' and op.checksum is not None:
                checksums.append(bytes(op.checksum.sync))
        return hashlib.sha1(b''.join(checksums)).hexdigest()

    def get_map(self):
        """Get the map name.

        TODO: Search all language strings.
        """
        map_id = self._header.scenario.game_settings.map_id
        instructions = self._header.scenario.messages.instructions
        size = mgz.const.MAP_SIZES[self._header.map_info.size_x]
        if map_id in mgz.const.MAP_NAMES:
            return mgz.const.MAP_NAMES[map_id], size
        else:
            name = 'Unknown'
            line = instructions.split('\n')[2]
            if line.find(':') > 0:
                name = line.split(":")[1].strip()
            elif line.find('\xa1\x47') > 0:
                name = line.split('\xa1\x47')[1].strip()
            elif line.find("\xa3\xba") > 0:
                name = line.split('\xa3\xba')[1].strip()
            name = name.strip()
            # Special case for maps (prefixed with language-specific name,
            # real map name in parentheses.
            if name.find(' (') > 0:
                name = name.split(' (')[1][:-1]
            return name, size
