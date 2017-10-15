"""Sync."""

# pylint: disable=too-few-public-methods
class Sync():
    """Synchronization wrapper."""

    def __init__(self, structure):
        """Initialize."""
        self._view = structure.view

    def __repr__(self):
        """Printable representation."""
        return ','.join([str(self._view.x), str(self._view.y)])
