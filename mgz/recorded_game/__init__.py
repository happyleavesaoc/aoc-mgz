"""Parse a recorded game.

Parses an "mgz" recorded game, extracts notable information,
and computes a variety of useful metadata.
"""

import datetime
import hashlib
import os.path
import re
from collections import defaultdict, Counter
from construct.core import ConstructError

import voobly

import mgz
import mgz.body
import mgz.const
import mgz.util
from mgz.recorded_game.chat import ChatMessage
from mgz.recorded_game.map import Map
from mgz.recorded_game.sync import Sync
from mgz.recorded_game.action import Action, ACTIONS_WITH_PLAYER_ID


VOOBLY_LADDERS = {
    'RM 1v1': 131,
    'RM TG': 132,
    'DM 1v1': 163,
    'DM TG': 162
}
MATCH_DATE = '(?P<year>[0-9]{4}).*?(?P<month>[0-9]{2}).*?(?P<day>[0-9]{2})'


class MgzError(Exception):
    """MGZ error."""

    pass


def _timestamp_to_time(timestamp):
    """Convert string timestamp to datetime.time."""
    if not timestamp:
        return
    return datetime.datetime.strptime(timestamp, '%H:%M:%S').time()


def _find_date(filename):
    """Find date in recorded game default(ish) filename."""
    has_date = re.search(MATCH_DATE, filename)
    if has_date:
        year = has_date.group('year')
        month = has_date.group('month')
        day = has_date.group('day')
        if int(year) > 2000 and int(month) in range(1, 13) and int(day) in range(1, 32):
            return '{}-{}-{}'.format(year, month, day)


def _calculate_apm(index, player_actions, other_actions, duration):
    """Calculate player's rAPM."""
    apm_per_player = {}
    for player_index, histogram in player_actions.items():
        apm_per_player[player_index] = sum(histogram.values())
    total_unattributed = sum(other_actions.values())
    total_attributed = sum(apm_per_player.values())
    player_proportion = apm_per_player[index] / total_attributed
    player_unattributed = total_unattributed * player_proportion
    apm = (apm_per_player[index] + player_unattributed) / (duration / 60)
    return int(apm)


# pylint: disable=too-many-instance-attributes, too-many-arguments
class RecordedGame():
    """Recorded game wrapper."""

    def __init__(self, path, voobly_api_key=None, chat=False, timeline=False, coords=False):
        """Initialize."""
        self._show_chat = chat
        self._show_timeline = timeline
        self._show_coords = coords
        self._handle = open(path, 'rb')
        self._hash = hashlib.sha1(self._handle.read()).hexdigest()
        self._eof = self._handle.tell()
        self._handle.seek(0)
        try:
            self._header = mgz.header.parse_stream(self._handle)
        except (ConstructError, ValueError):
            raise MgzError('failed to parse header')
        self._body_position = self._handle.tell()
        self._time = 0
        self._achievements_summarized = False
        self._ladder = None
        self._ratings = {}

        self._research = defaultdict(list)
        self._build = defaultdict(list)
        self._queue = []

        self._chat = []
        self._path = path
        self._num_players()
        self._timeline = []
        self._actions_by_player = defaultdict(Counter)
        self._actions_without_player = Counter()
        self._coords = []
        self._compute_diplomacy()
        self._voobly_session = voobly.get_session(voobly_api_key)
        self._summary = {}
        self._map = Map(self._header.scenario.game_settings.map_id, self._header.map_info.size_x,
                        self._header.map_info.size_y, self._header.scenario.messages.instructions)
        self._parse_lobby_chat(self._header.lobby.messages, 'lobby', '00:00:00')

    def _num_players(self):
        """Compute number of players, both human and computer."""
        self._player_num = 0
        self._computer_num = 0
        for player in self._header.scenario.game_settings.player_info:
            if player.type == 'human':
                self._player_num += 1
            elif player.type == 'computer':
                self._computer_num += 1

    def _parse_lobby_chat(self, messages, source, timestamp):
        """Parse a lobby chat message."""
        for message in messages:
            if message.message_length == 0:
                continue
            chat = ChatMessage(message.message, timestamp, self._players(), source=source)
            self._parse_chat(chat)

    def _parse_action(self, action, current_time):
        """Parse a player action.

        TODO: handle cancels
        """
        if action.action_type == 'research':
            name = mgz.const.TECHNOLOGIES[action.data.technology_type]
            self._research[action.data.player_id].append({
                'technology': name,
                'timestamp': _timestamp_to_time(action.timestamp)
            })
        elif action.action_type == 'build':
            self._build[action.data.player_id].append({
                'building': mgz.const.UNITS[action.data.building_type],
                'timestamp': _timestamp_to_time(current_time),
                'coordinates': {'x': action.data.x, 'y': action.data.y}
            })
        elif action.action_type == 'queue':
            for _ in range(0, int(action.data.number)):
                self._queue.append({
                    'unit': mgz.const.UNITS[action.data.unit_type],
                    'timestamp': _timestamp_to_time(current_time)
                })

    # pylint: disable=too-many-branches
    def operations(self, op_types=None):
        """Process operation stream."""
        if not op_types:
            op_types = ['message', 'action', 'sync', 'savedchapter']
        while self._handle.tell() < self._eof:
            current_time = mgz.util.convert_to_timestamp(self._time / 1000)
            try:
                operation = mgz.body.operation.parse_stream(self._handle)
            except (ConstructError, ValueError):
                raise MgzError('failed to parse body operation')
            if operation.type == 'action':
                if operation.action.type in ACTIONS_WITH_PLAYER_ID:
                    counter = self._actions_by_player[operation.action.player_id]
                    counter.update([operation.action.type])
                else:
                    self._actions_without_player.update([operation.action.type])
            if operation.type == 'action' and isinstance(operation.action.type, int):
                print(operation.action)
            if operation.type == 'sync':
                self._time += operation.time_increment
            if operation.type == 'action' and operation.action.type == 'postgame':
                self._summarize(operation)
            if operation.type == 'action':
                action = Action(operation, current_time)
                self._parse_action(action, current_time)
            if operation.type == 'savedchapter':
                # fix: Don't load messages we already saw in header or prev saved chapters
                self._parse_lobby_chat(operation.lobby.messages, 'save', current_time)
            if operation.type == 'sync':
                yield Sync(operation)
            elif operation.type == 'action' and operation.action.type != 'postgame':
                yield Action(operation, current_time)
            elif operation.type == 'message' and operation.subtype == 'chat':
                chat = ChatMessage(operation.data.text, current_time,
                                   self._players(), self._diplomacy['type'], 'game')
                self._parse_chat(chat)
                yield chat

    def reset(self):
        """Reset operation stream."""
        self._time = 0
        self._handle.seek(self._body_position)

    def summarize(self):
        """Summarize game."""
        if not self._achievements_summarized:
            for _ in self.operations():
                pass
        if not self._summary:
            raise MgzError('no postgame found')
        return self._summary

    def is_nomad(self):
        """Is this game nomad.

        TODO: Can we get from UP 1.4 achievements?
        """
        nomad = self._header.initial.restore_time == 0 or None
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'building' and obj.object_type == 'tc_1':
                    return False
        return nomad

    def is_regicide(self):
        """Is this game regicide."""
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'unit' and obj.object_type == 'king':
                    return True
        return False

    def is_arena(self):
        """Is this game arena.

        TODO: include hideout?
        """
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'building' and obj.object_type == 'stone_wall':
                    return True
        return False

    def _parse_chat(self, chat):
        """Parse a chat message."""
        if chat.data['type'] == 'chat':
            if chat.data['player'] in [p.player_name for i, p in self._players()]:
                self._chat.append(chat.data)
        elif chat.data['type'] == 'ladder':
            self._ladder = chat.data['ladder']
        elif chat.data['type'] == 'rating':
            if chat.data['rating'] != 1600:
                self._ratings[chat.data['player']] = chat.data['rating']

    def _parse_player(self, index, attributes, postgame, game_type):
        """Parse a player."""
        achievements = postgame.achievements[index - 1]
        try:
            voobly_user = voobly.user(self._voobly_session, attributes.player_name,
                                      ladder_ids=VOOBLY_LADDERS.values())
            voobly_ladder = '{} {}'.format(game_type, self._diplomacy['type'])
            voobly_ladder_id = VOOBLY_LADDERS.get(voobly_ladder)
            if voobly_ladder_id in voobly_user['ladders']:
                voobly_rating = voobly_user['ladders'].get(voobly_ladder_id).get('rating')
            else:
                voobly_rating = None
        except voobly.VooblyError:
            voobly_user = None
            voobly_rating = None
        return {
            'index': index,
            'number': attributes.player_color + 1,
            'color': mgz.const.PLAYER_COLORS[attributes.player_color],
            'coordinates': {
                'x': attributes.camera_x,
                'y': attributes.camera_y
            },
            'action_histogram': dict(self._actions_by_player[index]),
            'apm': _calculate_apm(index, self._actions_by_player,
                                  self._actions_without_player, postgame.duration_int),
            'name': attributes.player_name,
            'civilization': mgz.const.CIVILIZATION_NAMES[attributes.civilization],
            'position': self._compass_position(attributes.camera_x, attributes.camera_y),
            'score': achievements.total_score,
            'mvp': achievements.mvp,
            'winner': achievements.victory,
            'research': self._research.get(index, []),
            'build': self._build.get(index),
            'achievements': {
                'units_killed': achievements.military.units_killed,
                'units_lost': achievements.military.units_lost,
                'buildings_razed': achievements.military.buildings_razed,
                'buildings_lost': achievements.military.buildings_lost,
                'conversions': achievements.military.units_converted,
                'food_collected': achievements.economy.food_collected,
                'wood_collected': achievements.economy.wood_collected,
                'gold_collected': achievements.economy.gold_collected,
                'stone_collected': achievements.economy.stone_collected,
                'tribute_sent': achievements.economy.tribute_sent,
                'tribute_received': achievements.economy.tribute_received,
                'trade_gold': achievements.economy.trade_gold,
                'relic_gold': achievements.economy.relic_gold,
                'explored_percent': achievements.technology.explored_percent,
                'total_castles': achievements.society.total_castles,
                'relics_collected': achievements.society.relics_captured,
                'villager_high': achievements.society.villager_high
            },
            'ages': {
                'feudal': _timestamp_to_time(achievements.technology.feudal_time),
                'castle': _timestamp_to_time(achievements.technology.castle_time),
                'imperial': _timestamp_to_time(achievements.technology.imperial_time)
            },
            'voobly': {
                'rating_game': self._ratings.get(attributes.player_name),
                'rating_current': voobly_rating,
                'nation': voobly_user['nationid'] if voobly_user else None,
                'uid': voobly_user['uid'] if voobly_user else None
            }
        }

    def _compass_position(self, player_x, player_y):
        """Get compass position of player."""
        map_dim = self._map.size_x
        third = map_dim * (1/3.0)
        for direction in mgz.const.COMPASS:
            point = mgz.const.COMPASS[direction]
            xlower = point[0] * map_dim
            xupper = (point[0] * map_dim) + third
            ylower = point[1] * map_dim
            yupper = (point[1] * map_dim) + third
            if (player_x >= xlower and player_x < xupper and
                    player_y >= ylower and player_y < yupper):
                return direction

    def _players(self):
        """Get player attributes with index. No Gaia."""
        for i in range(1, self._header.replay.num_players):
            yield i, self._header.initial.players[i].attributes

    def players(self, postgame, game_type):
        """Return parsed players."""
        for i, attributes in self._players():
            yield self._parse_player(i, attributes, postgame, game_type)

    def teams(self):
        """Get list of teams."""
        teams = {}
        default_team = 1
        for i in range(1, self._header.replay.num_players):
            attributes = self._header.initial.players[i].attributes
            team = self._header.lobby.teams[i - 1]
            if team == 1:
                team = default_team
                default_team += 1
            if team not in teams:
                teams[team] = {'player_numbers': []}
            teams[team]['player_numbers'].append(attributes.player_color + 1)
        return list(teams.values())

    def _compute_diplomacy(self):
        """Compute diplomacy."""
        self._diplomacy = {
            'teams': self.teams(),
            'ffa': len(self.teams()) == (self._player_num + self._computer_num and
                                         self._player_num + self._computer_num > 2),
            'TG':  len(self.teams()) == 2 and self._player_num + self._computer_num > 2,
            '1v1': self._player_num + self._computer_num == 2,
        }
        self._diplomacy['type'] = 'unknown'
        if self._diplomacy['ffa']:
            self._diplomacy['type'] = 'ffa'
        if self._diplomacy['TG']:
            self._diplomacy['type'] = 'TG'
            size = len(self.teams()[0]['player_numbers'])
            self._diplomacy['team_size'] = '{}v{}'.format(size, size)
        if self._diplomacy['1v1']:
            self._diplomacy['type'] = '1v1'

    def _won_in(self):
        """Get age the game was won in."""
        if not self._summary['finished']:
            return
        starting_age = self._summary['settings']['starting_age'].lower()
        if starting_age == 'post imperial':
            starting_age = 'imperial'
        ages_reached = set([starting_age])
        for player in self._summary['players']:
            for age, reached in player['ages'].items():
                if reached:
                    ages_reached.add(age)
        ages = ['imperial', 'castle', 'feudal', 'dark']
        for age in ages:
            if age in ages_reached:
                return age

    def _rec_owner_number(self):
        """Get rec owner number."""
        player = self._header.initial.players[self._header.replay.rec_player]
        return player.attributes.player_color + 1

    # pylint: disable=no-self-use
    def _get_starting_age(self, data):
        """Get starting age."""
        if data.starting_age not in ['postimperial', 'dmpostimperial']:
            return data.starting_age.title()
        return 'Post Imperial'

    def _get_timestamp(self):
        """Get modification timestamp from rec file."""
        filename_date = _find_date(os.path.basename(self._path))
        if filename_date:
            return filename_date

    def _is_wololokingdoms(self):
        sample = self._header.initial.players[0].attributes.player_stats
        if 'trickle_food' in sample and sample.trickle_food:
            return True
        return False

    def _set_winning_team(self):
        """Mark the winning team."""
        if not self._summary['finished']:
            return
        for team in self._summary['diplomacy']['teams']:
            team['winner'] = False
            for player_number in team['player_numbers']:
                for player in self._summary['players']:
                    if player_number == player['number']:
                        if player['winner']:
                            team['winner'] = True

    def _map_hash(self):
        """Compute a map hash based on a combination of map attributes.

        - Elevation
        - Map name
        - Player names, colors, and civilizations
        """
        elevation_bytes = bytes([tile.elevation for tile in self._header.map_info.tile])
        map_name_bytes = self._map.name().encode()
        player_bytes = b''
        for _, attributes in self._players():
            player_bytes += (mgz.const.PLAYER_COLORS[attributes.player_color].encode() +
                             attributes.player_name.encode() +
                             mgz.const.CIVILIZATION_NAMES[attributes.civilization].encode())
        return hashlib.sha1(elevation_bytes + map_name_bytes + player_bytes).hexdigest()

    def _summarize(self, postgame):
        """Game summary implementation."""
        self._achievements_summarized = True
        data = postgame.action
        game_type = 'DM' if data.is_deathmatch else 'RM'
        self._summary = {
            'players': list(self.players(data, game_type)),
            'diplomacy': self._diplomacy,
            'rec_owner_index': self._header.replay.rec_player,
            'rec_owner_number': self._rec_owner_number(),
            'settings': {
                'type': game_type,
                'difficulty': self._header.scenario.game_settings.difficulty,
                'resource_level': data.resource_level,
                'population_limit': self._header.lobby.population_limit * 25,
                'speed': mgz.const.SPEEDS.get(self._header.replay.game_speed),
                'reveal_map': data.reveal_map,
                'starting_age': self._get_starting_age(data),
                'victory_condition': data.victory_type,
                'team_together': not data.team_together,
                'all_technologies': data.all_techs,
                'cheats': data.cheats,
                'lock_teams': data.lock_teams,
                'lock_speed': data.lock_speed,
                'record_game': True
            },
            'map': {
                'name': self._map.name(),
                'size': self._map.size(),
                'x': self._header.map_info.size_x,
                'y': self._header.map_info.size_y,
                'nomad': self.is_nomad(),
                'regicide': self.is_regicide(),
                'arena': self.is_arena(),
                'hash': self._map_hash()
            },
            'mods': {
                'wololokingdoms': self._is_wololokingdoms(),
            },
            'restore': {
                'restored': self._header.initial.restore_time > 0,
                'start_int': self._header.initial.restore_time,
                'start_time': mgz.util.convert_to_timestamp(self._header.initial.restore_time /
                                                            1000)
            },
            'voobly': {
                'ladder': self._ladder,
                'rated': self._ladder != None
            },
            'number_of_humans': data.player_num,
            'number_of_ai': data.computer_num,
            'duration': data.duration,
            'time_int': self._time,
            'finished': data.complete,
            'metadata': {
                'hash': self._hash,
                'version': mgz.const.VERSIONS[self._header.version],
                'sub_version': round(self._header.sub_version, 2),
                'filename': os.path.basename(self._path),
                'timestamp': self._get_timestamp()
            },
            'action_histogram': dict(self._actions_without_player),
            'queue': self._queue
        }
        if data.complete:
            self._summary['won_in'] = self._won_in().title()
            self._set_winning_team()
        if self._show_chat:
            self._summary['chat'] = self._chat
        if self._show_timeline:
            self._summary['timeline'] = self._timeline
        if self._show_coords:
            self._summary['coords'] = self._coords
