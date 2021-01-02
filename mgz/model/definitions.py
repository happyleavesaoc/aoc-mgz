"""Model class definitions."""

from dataclasses import dataclass
from datetime import timedelta
from mgz.util import Version


@dataclass
class Object:
    """Represents an object."""

    name: str
    instance_id: int
    x: float
    y: float


@dataclass
class Player:
    """Represents a player."""

    number: int
    name: str
    color: str
    civilization: str
    objects: list
    profile_id: int
    team: list = None
    winner: bool = False

    def __repr__(self):
        return self.name

@dataclass
class Tile:
    """Represents a map tile."""

    terrain: int
    elevation: int
    x: int
    y: int


@dataclass
class Map:
    """Represents a map."""

    name: str
    dimension: int
    size: str
    custom: bool
    seed: int
    tiles: list

    def __repr__(self):
        return self.name

@dataclass
class File:
    """Represents the recorded game file."""

    encoding: str
    language: str
    perspective: Player


@dataclass
class Chat:
    """Represents a chat message."""

    timestamp: timedelta
    message: str
    player: Player

    def __repr__(self):
        return f'[{self.timestamp}] {self.player}: {self.message}'


@dataclass
class Match:
    """Represents a match."""

    players: list
    teams: list
    map: Map
    file: File
    speed: str
    cheats: bool
    lock_teams: bool
    population: int
    chat: list
    guid: str
    lobby: str
    dataset: str
    type: str
    map_reveal: str
    duration: timedelta
    diplomacy_type: str
    version: Version
