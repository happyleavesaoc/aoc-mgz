import json
import unittest
from mgz.model import parse_match, serialize


class TestSerialize(unittest.TestCase):
    """Test serialization of match data for player references."""

    @classmethod
    def setUpClass(cls):
        with open('tests/recs/de-13.34.aoe2record', 'rb') as handle:
            cls.serialized = serialize(parse_match(handle))

    def test_players_are_dicts(self):
        """Players serialize as full dict objects."""
        players = self.serialized['players']
        self.assertIsInstance(players, list)
        self.assertGreater(len(players), 0)
        for player in players:
            self.assertIsInstance(player, dict)
            self.assertIn('number', player)
            self.assertIn('name', player)

    def test_team_references_are_integers(self):
        """Team lists contain only integers, not Player objects."""
        for player in self.serialized['players']:
            if 'team' not in player:
                continue
            team = player['team']
            self.assertIsInstance(team, list)
            for member in team:
                self.assertIsInstance(member, int,
                    f"Player {player['number']} team has non-integer: {type(member).__name__}")

    def test_no_circular_references(self):
        """Serialized data has no circular references."""
        try:
            json.dumps(self.serialized)
        except (TypeError, ValueError) as e:
            self.fail(f"Circular reference detected: {e}")


if __name__ == '__main__':
    unittest.main()
