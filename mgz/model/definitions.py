"""Model class definitions."""

from dataclasses import dataclass
from datetime import timedelta
from mgz.fast import Action as ActionEnum
from mgz.util import Version


@dataclass
class Position:
    """Represents a coordinate."""

    x: float
    y: float


@dataclass
class Object:
    """Represents an object."""

    name: str
    instance_id: int
    position: Position


@dataclass
class Player:
    """Represents a player."""

    number: int
    name: str
    color: str
    civilization: str
    position: Position
    objects: list
    profile_id: int
    team: list = None
    winner: bool = False

    def __repr__(self):
        return self.name

    def __hash__(self):
        return self.number


@dataclass
class Action:
    """Represents an abstract action."""

    timestamp: timedelta
    type: ActionEnum
    payload: dict
    player: Player = None
    position: Position = None


@dataclass
class Viewlock:
    """Represents player view."""

    timestamp: timedelta
    position: Position


@dataclass
class Tile:
    """Represents a map tile."""

    terrain: int
    elevation: int
    position: Position


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
    viewlocks: list


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
    gaia: list
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
    actions: list
