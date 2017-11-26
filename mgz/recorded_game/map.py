"""Map."""

import mgz.const


class Map():
    """Map wrapper."""

    def __init__(self, map_id, x, y, instructions):
        """Initialize."""
        self.size_x = x
        self.size_y = y
        self._size = mgz.const.MAP_SIZES[x]
        if map_id in mgz.const.MAP_NAMES:
            self._name = mgz.const.MAP_NAMES[map_id]
        else:
            self._name = 'Unknown'
            line = instructions.split('\n')[2]
            if line.find(':') > 0:
                self._name = line.split(":")[1].strip()
            elif line.find('\xa1\x47') > 0:
                self._name = line.split('\xa1\x47')[1].strip()
            elif line.find("\xa3\xba") > 0:
                self._name = line.split('\xa3\xba')[1].strip()
            self._name = self._name.strip()
            # Special case for nomad maps (prefixed with
            #   language-specific name, real map name in
            #   parentheses.
            if self._name.find(' (') > 0 and self._name.find('Nomad') > -1:
                self._name = self._name.split(' (')[1][:-1]

    def name(self):
        """Get map name."""
        return self._name

    def size(self):
        """Get map size."""
        return self._size

    def __repr__(self):
        """Get printable representation."""
        return self._name
