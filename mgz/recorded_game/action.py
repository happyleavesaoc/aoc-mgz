"""Actions."""


ACTIONS_WITH_PLAYER_ID = [
    'interact', 'move', 'resign', 'formation', 'research', 'build',
    'game', 'wall', 'delete', 'tribute', 'flare', 'sell', 'buy', 'chapter'
]


# pylint: disable=too-few-public-methods
class Action():
    """Action wrapper."""

    def __init__(self, structure, timestamp):
        """Initialize."""
        self.timestamp = timestamp
        self.action_type = structure.action.type
        self.data = structure.action

    def __repr__(self):
        """Printable representation."""
        return self.action_type
