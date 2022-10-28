"""Model class definitions."""

from dataclasses import dataclass
from datetime import timedelta, datetime
from mgz.fast import Action as ActionEnum
from mgz.util import Version


@dataclass
class Position:
    """Represents a coordinate."""

    x: float
    y: float

    def hash(self):
        return hash((self.x, self.y))


@dataclass
class Object:
    """Represents an object."""

    name: str
    class_id: int
    object_id: int
    instance_id: int
    index: int
    position: Position


@dataclass
class Player:
    """Represents a player."""

    number: int
    name: str
    color: str
    color_id: int
    civilization: str
    civilization_id: int
    position: Position
    objects: list
    profile_id: int
    prefer_random: bool = None
    team: list = None
    winner: bool = False
    eapm: int = None

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
class Input:
    """Represents a player input."""

    timestamp: timedelta
    type: str
    param: str
    payload: dict
    player: Player = None
    position: Position = None


@dataclass
class Viewlock:
    """Represents player view."""

    timestamp: timedelta
    position: Position
    player: Player


@dataclass
class Tile:
    """Represents a map tile."""

    terrain: int
    elevation: int
    position: Position


@dataclass
class Map:
    """Represents a map."""

    id: int
    name: str
    dimension: int
    size: str
    custom: bool
    seed: int
    mod_id: int
    zr: bool
    modes: dict
    tiles: list

    def __repr__(self):
        return self.name

@dataclass
class File:
    """Represents the recorded game file."""

    encoding: str
    language: str
    hash: str
    size: int
    perspective: Player
    viewlocks: list


@dataclass
class Chat:
    """Represents a chat message."""

    timestamp: timedelta
    message: str
    origination: str
    audience: str
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
    restored: bool
    restored_at: timedelta
    speed: str
    speed_id: int
    cheats: bool
    lock_teams: bool
    population: int
    chat: list
    guid: str
    lobby: str
    dataset: str
    type: str
    type_id: int
    map_reveal: str
    map_reveal_id: int
    difficulty: str
    difficulty_id: int
    starting_age: str
    starting_age_id: int
    team_together: bool
    lock_speed: bool
    all_technologies: bool
    multiqueue: bool
    duration: timedelta
    diplomacy_type: str
    completed: bool
    version: Version
    game_version: str
    save_version: float
    log_version: int
    build_version: int
    timestamp: datetime
    spec_delay: timedelta
    allow_specs: bool
    hidden_civs: bool
    private: bool
    hash: str
    actions: list
    inputs: list
