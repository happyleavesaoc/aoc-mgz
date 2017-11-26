"""MGZ parsing utilities."""

import struct
import zlib
from io import BytesIO

import construct.core
from construct import Adapter, Construct, Subconstruct, Tunnel

# pylint: disable=abstract-method,protected-access


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
        return zlib.decompressobj().decompress(b'x\x9c' + data)


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


class Find(Construct):
    """Find bytes, and read past them."""

    __slots__ = ["find", "max_length"]

    def __init__(self, find, max_length):
        """Initiallize."""
        Construct.__init__(self)
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
        skip = read_bytes.find(self.find) + len(self.find)
        stream.seek(start + skip)
        return skip


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
            else:
                subobj = self.subcon._parse(stream, context, path)
                objs.append(subobj)
        return objs


class GotoObjectsEnd(Construct):
    """Find the end of a player's objects list.

    Necessary since we can't parse objects from a resume game (yet).
    """

    def _parse(self, stream, context, path):
        """Parse until the end of objects data."""
        num_players = context._._._.replay.num_players
        start = stream.tell()
        # Have to read everything to be able to use find()
        read_bytes = stream.read()
        # Try to find the first marker, a portion of the next player structure
        marker_up14 = read_bytes.find(b"\x16\xc6\x00\x00\x00\x21")
        marker_up15 = read_bytes.find(b"\x16\xf0\x00\x00\x00\x21")
        marker = -1
        if marker_up14 > 0 and marker_up15 < 0:
            marker = marker_up14
        elif marker_up15 > 0 and marker_up14 < 0:
            marker = marker_up15
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
            marker = read_bytes.find(b"\xf6\x28\x9c\x3f")
            # Backtrack through the achievements and initial structure footer
            backtrack = ((1817 * (num_players - 1)) + 4 + 19)
        # Seek to the position we found
        end = start + marker - backtrack
        stream.seek(end)
        return end
