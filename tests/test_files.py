import glob
import unittest
from mgz import header, body, fast


def parse_file_full(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        eof = f.tell()
        f.seek(0)
        h = header.parse_stream(f)
        body.meta.parse_stream(f)
        while f.tell() < eof:
            body.operation.parse_stream(f)


def parse_file_fast(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        eof = f.tell()
        f.seek(0)
        h = header.parse_stream(f)
        fast.meta(f)
        while f.tell() < eof:
            fast.operation(f)


class TestFiles(unittest.TestCase):

    def test_files_full(self):
        parse_file_full('tests/recs/small.mgz')
        parse_file_full('tests/recs/de-13.07.aoe2record')

    def test_files_fast(self):
        # these files aren't supported by full header parser for now:
        skip = {"tests/recs/de-50.6-scenario.aoe2record", "tests/recs/de-50.6-scenario-with-triggers.aoe2record"}

        for path in glob.glob('tests/recs/*'):
            if path in skip:
                continue
            parse_file_fast(path)
