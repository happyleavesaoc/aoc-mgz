"""MGZ parsing utilities."""

import logging
import struct
import zlib
from enum import Enum
from io import BytesIO

import construct.core
from construct import Adapter, Construct, Subconstruct, Tunnel

from mgz import const


# pylint: disable=abstract-method,protected-access

LOGGER = logging.getLogger(__name__)
SEARCH_MAX_BYTES = 3000
POSTGAME_LENGTH = 2096
LOOKAHEAD = 9


class Version(Enum):
    """Version enumeration.

    Using consts from https://github.com/goto-bus-stop/recanalyst/blob/master/src/Model/Version.php
    for consistency.
    """
    AOK = 1
    AOC = 4
    AOC10 = 5
    AOC10C = 8
    USERPATCH12 = 12
    USERPATCH13 = 13
    USERPATCH14 = 11
    USERPATCH15 = 20
    DE = 21
    USERPATCH14RC2 = 22
    MCP = 30


class MgzPrefixed(Subconstruct):
    """Like `Prefixed`, but accepting arbitrary length."""

    __slots__ = ["name", "length", "subcon"]

    def __init__(self, length, subcon):
        """Initialize."""
        super(MgzPrefixed, self).__init__(subcon)
        self.length = length

    def _parse(self, stream, context, path):
        """Parse tunnel."""
        length = self.length(context)
        new_stream = BytesIO(construct.core._read_stream(stream, length))
        return self.subcon._parse(new_stream, context, path)


class ZlibCompressed(Tunnel):
    """Like Compressed, but only does header-less zlib."""

    __slots__ = []

    def _decode(self, data, context):
        """Decode zlib without header bytes."""
        return zlib.decompress(data, wbits=-15)


def get_version(game_version, save_version, log_version):
    """Get version based on version fields."""
    if game_version == 'VER 9.3':
        return Version.AOK
    if game_version == 'VER 9.4':
        if log_version == 3:
            return Version.AOC10
        if log_version == 4:
            return Version.AOC10C
        if log_version == 5 or save_version >= 12.97:
            return Version.DE
        return Version.AOC
    if game_version == 'VER 9.8':
        return Version.USERPATCH12
    if game_version == 'VER 9.9':
        return Version.USERPATCH13
    if game_version == 'VER 9.A':
        return Version.USERPATCH14RC2
    if game_version in ['VER 9.B', 'VER 9.C', 'VER 9.D']:
        return Version.USERPATCH14
    if game_version in ['VER 9.E', 'VER 9.F']:
        return Version.USERPATCH15
    if game_version == 'MCP 9.F':
        return Version.MCP
    if log_version is not None or game_version != 'VER 9.4':
        raise ValueError('unsupported version: {}, {}, {}'.format(game_version, save_version, log_version))


def find_version(ctx):
    """Test version."""
    if 'version' not in ctx:
        return find_version(ctx._)
    return ctx.version


def find_save_version(ctx):
    """Test save version."""
    if 'save_version' not in ctx:
        return find_save_version(ctx._)
    return ctx.save_version


def check_flags(peek):
    """Check byte sequence for only flag bytes."""
    for i in peek:
        if i not in [0, 1]:
            return False
    return True


def convert_to_timestamp(time):
    """Convert int to timestamp string."""
    if time == -1:
        return None
    time = int(time*1000)
    hour = time//1000//3600
    minute = (time//1000//60) % 60
    second = (time//1000) % 60
    return str(hour).zfill(2)+":"+str(minute).zfill(2)+":"+str(second).zfill(2)


class TimeSecAdapter(Adapter):
    """Conversion to readable time."""

    def _decode(self, obj, context):
        """Decode timestamp to string."""
        return convert_to_timestamp(obj)


class BoolAdapter(Adapter):
    """Bools with potential padding."""

    def _decode(self, obj, context):
        """Decode bool."""
        return obj == 1


class VersionAdapter(Adapter):
    """Round save version."""

    def _decode(self, obj, context):
        """Decode by rounding float."""
        return round(obj, 2)


class ModVersionAdapter(Adapter):
    """Parse mod version."""

    def _decode(self, obj, context):
        """Decode mod."""
        number = int(obj)
        mod_id = int(number / 1000)
        mod_version = '.'.join(list(str(number % 1000)))
        return {
            'id': mod_id,
            'name': const.MODS.get(mod_id, 'Unknown Mod'),
            'version': mod_version
        }


class Find(Construct):
    """Find bytes, and read past them."""

    __slots__ = ["find", "max_length"]

    def __init__(self, find, max_length):
        """Initiallize."""
        Construct.__init__(self)
        if not isinstance(find, list):
            find = [find]
        self.find = find
        self.max_length = max_length

    def _parse(self, stream, context, path):
        """Parse stream to find a given byte string."""
        start = stream.tell()
        read_bytes = ""
        if self.max_length:
            read_bytes = stream.read(self.max_length)
        else:
            read_bytes = stream.read()
        for f in self.find:
            pos = read_bytes.find(f)
            if pos == -1:
                continue
            skip = pos + len(f)
            stream.seek(start + skip)
            return skip
        raise RuntimeError('could not find bytes')


class RepeatUpTo(Subconstruct):
    """Like RepeatUntil, but doesn't include the last element in the return value."""

    __slots__ = ["find"]

    def __init__(self, find, subcon):
        """Initialize."""
        Subconstruct.__init__(self, subcon)
        self.find = find

    def _parse(self, stream, context, path):
        """Parse until a given byte string is found."""
        objs = []
        while True:
            start = stream.tell()
            test = stream.read(len(self.find))
            stream.seek(start)
            if test == self.find:
                break
            subobj = self.subcon._parse(stream, context, path)
            objs.append(subobj)
        return objs


class GotoObjectsEnd(Construct):
    """Find the end of a player's objects list.

    Necessary since we can't parse objects from a resume game (yet).
    """

    # pylint: disable=chained-comparison, too-many-locals
    def _parse(self, stream, context, path):
        """Parse until the end of objects data."""
        num_players = context._._.replay.num_players
        marker_num = context.attributes.num_header_data
        save_version = context._._.save_version
        start = stream.tell()
        # Have to read everything to be able to use find()
        read_bytes = stream.read()
        # Try to find the first marker, a portion of the next player structure
        # The byte that changes is the number of player stats fields
        marker = read_bytes.find(b'\x16' + struct.pack('<I', int(marker_num)) + b'\x21')
        # If it exists, we're not on the last player yet
        if marker > 0:
            # Backtrack through the player name
            count = 0
            while struct.unpack("<H", read_bytes[marker-2:marker])[0] != count:
                marker -= 1
                count += 1
            # Backtrack through the rest of the next player structure
            backtrack = 43 + num_players
        # Otherwise, this is the last player
        else:
            # Search for the scenario header
            # TODO: make this section more reliable
            marker_aok = read_bytes.find(b"\x9a\x99\x99\x3f")
            marker_up = read_bytes.find(b"\xf6\x28\x9c\x3f")
            if save_version >= 13.07:
                marker_de = read_bytes.find(b"\x29\x5c\xaf\x3f")
            else:
                marker_de = read_bytes.find(b"\x7b\x14\xae\x3f")
            if marker_up > 0 and marker_de < 0: # aok marker can appear in up
                marker = marker_up
            elif marker_de > 0 and marker_up < 0 and marker_aok < 0:
                marker = marker_de
            elif marker_aok > 0 and marker_up < 0 and marker_de < 0:
                marker = marker_aok
            # Backtrack through the achievements and initial structure footer
            backtrack = ((1817 * (num_players - 1)) + 4 + 19)
        # Seek to the position we found
        end = start + marker - backtrack - 2
        stream.seek(end)
        return end


def find_postgame(data, size):
    """Find postgame and grab duration.

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
    return None, None
