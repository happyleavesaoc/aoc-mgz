import codecs
import unittest
from mgz.model import parse_match
from mgz.util import Version

class TestModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/small.mgz', 'rb') as handle:
            cls.match = parse_match(handle)

    def test_match(self):
        self.assertEqual(self.match.speed, 'Standard')
        self.assertEqual(self.match.population, 200)
        self.assertEqual(self.match.diplomacy_type, '1v1')
        self.assertEqual(self.match.type, 'Random Map')
        self.assertEqual(self.match.dataset, 'Wololo Kingdoms')
        self.assertEqual(self.match.version, Version.USERPATCH15)

    def test_players(self):
        players = self.match.players
        self.assertEqual(len(players), 2)
        self.assertEqual(players[0].name, '[Heresy]LaaaaaN')
        self.assertEqual(players[0].number, 1)
        self.assertEqual(players[0].color, 'Red')
        self.assertEqual(players[0].civilization, 'Malians')
        self.assertFalse(players[0].winner)

    def test_objects(self):
        objects = self.match.players[0].objects
        self.assertEqual(len([o for o in objects if o.name == 'Villager']), 3)

    def test_map(self):
        self.assertEqual(self.match.map.name, 'KotD2 - Arabia')
        self.assertEqual(self.match.map.dimension, 120)
        self.assertEqual(self.match.map.size, 'Tiny')
        self.assertEqual(self.match.map.seed, -2119451194)
        self.assertEqual(len(self.match.map.tiles), 120 * 120)
        self.assertTrue(self.match.map.custom)

    def test_file(self):
        self.assertEqual(self.match.file.encoding, codecs.lookup('latin-1'))
        self.assertEqual(self.match.file.language, 'es')
        self.assertEqual(self.match.file.perspective.name, '[Heresy]LaaaaaN')
