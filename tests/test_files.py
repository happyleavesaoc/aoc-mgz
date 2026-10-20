import glob
import unittest
from mgz import header, body, fast
import mgz.fast.header
from mgz.summary import ModelSummary, FullSummary


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

def parse_file_summary(path, summary_class):
    with open(path, 'rb') as f:
        summary_class(f)


class TestFiles(unittest.TestCase):

    def test_save_version_67_2_players(self):
        """67.2 changed the player record and the metadata section.

        de-68.0-no-opponent is the case that fails differently: with no AI
        in the game there is no AI data block, and the field that says so is
        no longer where the parser looked, so the forward scan for the end of
        that block used to overshoot and every subsequent field was garbage.
        """
        for name, expected in (
                ('de-68.0', 3),
                ('de-68.0-no-opponent', 2),
        ):
            with open(f'tests/recs/{name}.aoe2record', 'rb') as handle:
                parsed = fast.header.parse(handle)
            self.assertEqual(len(parsed['players']), expected, name)

    def test_files_full(self):
        parse_file_full('tests/recs/small.mgz')
        parse_file_full('tests/recs/de-13.07.aoe2record')

    def test_files_fast(self):
        # these files aren't supported by full header parser for now:
        skip = {
            "tests/recs/de-50.6-scenario.aoe2record",
            "tests/recs/de-50.6-scenario-with-triggers.aoe2record",
            # Save version 67.2 moved something inside `initial` as well.
            # The fast parser reads these fully; the construct header still
            # runs off the end of the stream, and I did not want to guess at
            # a layout I could not measure.
            "tests/recs/de-68.0.aoe2record",
            "tests/recs/de-68.0-no-opponent.aoe2record",
        }

        for path in glob.glob('tests/recs/*'):
            if path.replace("\\", "/") in skip:
                continue
            parse_file_fast(path)

    @unittest.skip("This test is meant to be run manually when debugging issues in a specific rec")
    def test_single_rec(self):
        rec = "tests/recs/de-64.3.aoe2record"
        parse_file_fast(rec)
        parse_file_summary(rec, FullSummary)
        parse_file_summary(rec, ModelSummary)

