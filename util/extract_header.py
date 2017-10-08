"""Extract header from MGZ file."""

import sys
import struct
import zlib


with open(sys.argv[1], 'rb') as f:
    buf = f.read()
    (header_length, saved_chapter) = struct.unpack('<II', buf[0:8])
    subset = buf[8:header_length - 8]
    header = zlib.decompressobj().decompress(b'x\x9c' + subset)
    with open(sys.argv[2], 'wb') as out:
        out.write(header)
