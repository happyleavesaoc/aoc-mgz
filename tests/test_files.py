import glob
import unittest
from mgz import header, body, fast, Version
from mgz.fast.header import parse


def parse_file_full(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        eof = f.tell()
        f.seek(0)
        h = header.parse_stream(f)
        body.meta.parse_stream(f)
        while f.tell() < eof:
            body.operation.parse_stream(f)


def parse_file_full_header_fast_body(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        eof = f.tell()
        f.seek(0)
        h = header.parse_stream(f)
        fast.meta(f)
        while f.tell() < eof:
            fast.operation(f)


def parse_file_fast(path):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        eof = f.tell()
        f.seek(0)

        h = fast.header.parse(f)
        fast.meta(f)
        while f.tell() < eof:
            fast.operation(f)

        return h


class TestFiles(unittest.TestCase):

    def test_files_full(self):
        parse_file_full('tests/recs/small.mgz')
        parse_file_full('tests/recs/de-13.07.aoe2record')

    def test_files_full_header_fast_body(self):
        # these files aren't supported by full header parser for now:
        skip = {"tests/recs/de-50.6-scenario.aoe2record", "tests/recs/de-50.6-scenario-with-triggers.aoe2record",
                "tests/recs/de-61.5.aoe2record", "tests/recs/de-61.5-2.aoe2record", "tests/recs/de-61.5-3.aoe2record"}

        for path in glob.glob('tests/recs/*'):
            if path in skip:
                continue

            parse_file_full_header_fast_body(path)

    def test_de_files_fast_header_fast_body(self):
        for path in glob.glob('tests/recs/*'):
            # test only DE records after save version 13
            if not path.startswith("tests/recs/de") or \
                    path.startswith("tests/recs/de-12") or \
                    path.startswith("tests/recs/de-13"):
                continue

            h = parse_file_fast(path)

            self.assertEqual(h["version"], Version.DE)
            self.assertGreaterEqual(len(h["players"]), 1)
            self.assertIn(h["map"]["dimension"], (120, 144, 168, 200, 220, 240, 480))
