import unittest
from mgz.fast.header import parse
from mgz.util import Version

class TestFastUserPatch15(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/small.mgz', 'rb') as handle:
            cls.data = parse(handle)

    def test_version(self):
        self.assertEqual(self.data['version'], Version.USERPATCH15)

    def test_players(self):
        players = self.data.get('players')
        self.assertEqual(len(players), 3)
        self.assertEqual(players[0]['diplomacy'], [1, 4, 4, -1, -1, -1, -1, -1, -1])
        self.assertEqual(players[1]['diplomacy'], [0, 1, 4, -1, -1, -1, -1, -1, -1])
        self.assertEqual(players[2]['diplomacy'], [0, 4, 1, -1, -1, -1, -1, -1, -1])

    def test_map(self):
        self.assertEqual(self.data['scenario']['map_id'], 44)


class TestFastDE(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/de-13.34.aoe2record', 'rb') as handle:
            cls.data = parse(handle)

    def test_version(self):
        self.assertEqual(self.data['version'], Version.DE)

    def test_players(self):
        players = self.data.get('players')
        self.assertEqual(len(players), 3)

    def test_map(self):
        self.assertEqual(self.data['scenario']['map_id'], 9)
        self.assertEqual(self.data['lobby']['seed'], -1970180596)


class TestFastDEScenario(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/de-50.6-scenario.aoe2record', 'rb') as handle:
            cls.data = parse(handle)

    def test_version(self):
        self.assertEqual(self.data['version'], Version.DE)

    def test_players(self):
        players = self.data.get('players')
        self.assertEqual(len(players), 3)


class TestFastDEScenarioWithTriggers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/de-50.6-scenario-with-triggers.aoe2record', 'rb') as handle:
            cls.data = parse(handle)

    def test_version(self):
        self.assertEqual(self.data['version'], Version.DE)

    def test_players(self):
        players = self.data.get('players')
        self.assertEqual(len(players), 3)


class TestFastHD(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/hd-5.8.aoe2record', 'rb') as handle:
            cls.data = parse(handle)

    def test_version(self):
        self.assertEqual(self.data['version'], Version.HD)

    def test_players(self):
        players = self.data.get('players')
        self.assertEqual(len(players), 7)

    def test_map(self):
        self.assertEqual(self.data['scenario']['map_id'], 0)
