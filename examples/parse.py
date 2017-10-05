import sys
from mgz import header, body

if __name__ == "__main__":
    # For each input filename
    for arg in sys.argv[1:]:
        with open(arg, 'rb') as f:
            # Remember end of file
            f.seek(0, 2)
            eof = f.tell()
            f.seek(0)
            # Parse the header
            h = header.parse_stream(f)
            # Parse the body
            while f.tell() < eof:
                # Parse a body operation
                o = body.operation.parse_stream(f)
