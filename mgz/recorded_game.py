"""Parse a recorded game.

Parses an "mgz" recorded game, extracts notable information,
and computes a variety of useful metadata.
"""

import datetime
import os.path
from collections import defaultdict
import mgz
import mgz.body
import mgz.util
import mgz.const
import voobly


VOOBLY_LADDERS = {
    'RM 1v1': 131,
    'RM team_game': 132,
    'DM 1v1': 163,
    'DM team_game': 162
}


class ChatMessage():
    """Parse a chat message."""

    def __init__(self, line, timestamp, players, diplomacy_type=None):
        """Initalize."""
        self.data = {
            'timestamp': timestamp
        }
        if line.find('Voobly: Ratings provided') > 0:
            self._parse_ladder(line)
        elif line.find('Voobly') == 3:
            self._parse_voobly(line)
        elif line.find('<Rating>') > 0:
            self._parse_rating(line)
        elif line.find('@#0<') == 0:
            self._parse_injected(line)
        else:
            self._parse_chat(line, players, diplomacy_type)

    def _parse_ladder(self, line):
        start = line.find("'") + 1
        end = line.find("'", start)
        self.data.update({
            'type': 'ladder',
            'ladder': line[start:end]
        })

    def _parse_voobly(self, line):
        message = line[11:]
        self.data.update({
            'type': 'voobly',
            'message': message
        })

    def _parse_rating(self, line):
        player_start = line.find('>') + 2
        player_end = line.find(':', player_start)
        player = line[player_start:player_end]
        rating = int(line[player_end + 2:len(line)])
        self.data.update({
            'type': 'rating',
            'player': player,
            'rating': rating
        })

    def _parse_injected(self, line):
        prefix = ''
        if line.find('<Team>') > 0:
            line = line.replace('<Team>', '', 1)
            prefix = ';'
        source_start = line.find('<') + 1
        source_end = line.find('>', source_start)
        source = line[source_start:source_end]
        name_end = line.find(':', source_end)
        name = line[source_end + 2:name_end]
        message = line[name_end + 2:]
        self.data.update({
            'type': 'injected',
            'source': source.lower(),
            'name': name,
            'message': '{}{}'.format(prefix, message)
        })

    def _parse_chat(self, line, players, diplomacy_type):
        player_start = line.find('#') + 2
        player_end = line.find(':', player_start)
        player = line[player_start:player_end]
        if self.data['timestamp'] == '00:00:00':
            group = 'All'
        elif diplomacy_type == 'team_game':
            group = 'Team'
        else:
            group = 'All'
        if player.find('>') > 0:
            group = player[1:player.find('>')]
            player = player[player.find('>') + 1:]
        message = line[player_end + 2:]
        color = None
        for _, player_h in players:
            if player_h.player_name == player:
                color = mgz.const.PLAYER_COLORS[player_h.player_color]
        self.data.update({
            'type': 'chat',
            'player': player,
            'message': message,
            'color': color,
            'to': group.lower()
        })

    def __repr__(self):
        """Printable representation."""
        if self.data['type'] == 'chat':
            return '{} <{}> {}: {}'.format(self.data['timestamp'], self.data['to'], self.data['player'], self.data['message'])
        elif self.data['type'] == 'rating':
            return '{}: {}'.format(self.data['player'], self.data['rating'])
        elif self.data['type'] == 'ladder':
            return 'Ladder: {}'.format(self.data['ladder'])
        elif self.data['type'] == 'injected':
            return '{} <{}> {}: {}'.format(self.data['timestamp'], self.data['source'], self.data['name'], self.data['message'])
        elif self.data['type'] == 'voobly':
            return 'Voobly: {}'.format(self.data['message'])


class Sync():
    """Synchronization wrapper."""

    def __init__(self, structure):
        """Initialize."""
        self._view = structure.view

    def __repr__(self):
        """Printable representation."""
        return ','.join([str(self._view.x), str(self._view.y)])


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


class Map():
    """Map wrapper."""

    def __init__(self, map_id, x, y, instructions):
        """Initialize."""
        self.x = x
        self.y = y
        self._size = mgz.const.MAP_SIZES[x]
        if map_id in mgz.const.MAP_NAMES:
            self._name = mgz.const.MAP_NAMES[map_id]
        else:
            self._name = 'Unknown'
            line = instructions.split('\n')[2]
            if line.find(':') > 0:
                self._name = line.split(":")[1].strip()
            elif line.find(b'\xa1\x47') > 0:
                self._name = line.split(b'\xa1\x47')[1].strip()
            elif line.find(b"\xa3\xba") > 0:
                self._name = line.split(b'\xa3\xba')[1].strip()
            self._name = self._name.strip()

    def name(self):
        """Get map name."""
        return self._name

    def size(self):
        """Get map size."""
        return self._size

    def __repr__(self):
        """Get printable representation."""
        return self._name


class RecordedGame():
    """Recorded game wrapper."""

    def __init__(self, path, voobly_api_key=None):
        """Initialize."""
        self._handle = open(path, 'rb')
        self._handle.seek(0, 2)
        self._eof = self._handle.tell()
        self._handle.seek(0)
        self._header = mgz.header.parse_stream(self._handle)
        self._body_position = self._handle.tell()
        self._time = 0
        self._achievements_summarized = False
        self._ladder = None
        self._ratings = {}
        self._research = defaultdict(dict)
        self._chat = []
        self._path = path
        self._num_players()
        self._compute_diplomacy()
        self._voobly_session = voobly.get_session(voobly_api_key)
        self._summary = {}
        self._map = Map(self._header.scenario.game_settings.map_id, self._header.map_info.size_x, self._header.map_info.size_y, self._header.scenario.messages.instructions)
        self._parse_lobby_chat(self._header.lobby.messages)

    def _num_players(self):
        """Compute number of players, both human and computer."""
        self._player_num = 0
        self._computer_num = 0
        for player in self._header.scenario.game_settings.player_info:
            if player.type == 'human':
                self._player_num += 1
            elif player.type == 'computer':
                self._computer_num += 1

    def _parse_lobby_chat(self, messages):
        """Parse a lobby chat message."""
        for message in messages:
            if message.message_length == 0:
                continue
            chat = ChatMessage(message.message, '00:00:00', self._players())
            self._parse_chat(chat)

    def _parse_action(self, action):
        """Parse a player action."""
        if action.action_type == 'research':
            name = mgz.const.TECHNOLOGIES[action.data.technology_type]
            self._research[action.data.player_id][name] = action.timestamp
        # TODO: handle cancels


    def operations(self, op_types=None):
        """Process operation stream."""
        if not op_types:
            op_types = ['message', 'action', 'sync', 'savedchapter']
        while self._handle.tell() < self._eof:
            current_time = mgz.util.convert_to_timestamp(self._time / 1000)
            operation = mgz.body.operation.parse_stream(self._handle)
            if operation.type == 'sync':
                self._time += operation.time_increment
            if operation.type == 'action' and operation.action.type == 'postgame':
                self._summarize(operation)
            if operation.type == 'action':
                action = Action(operation, current_time)
                self._parse_action(action)
            if operation.type not in op_types:
                continue
            if operation.type == 'sync':
                yield Sync(operation)
            elif operation.type == 'action' and operation.action.type != 'postgame':
                yield Action(operation, current_time)
            elif operation.type == 'message' and operation.subtype == 'chat':
                chat = ChatMessage(operation.data.text, current_time, self._players(), self._diplomacy['type'])
                self._parse_chat(chat)
                yield chat

    def reset(self):
        """Reset operation stream."""
        self._time = 0
        self._handle.seek(self._body_position)

    def summarize(self):
        """Summarize game."""
        if not self._achievements_summarized:
            for _ in self.operations(): pass
        return self._summary

    def is_nomad(self):
        """Is this game nomad?

        TODO: Can we get from UP 1.4 achievements?
        """
        nomad = self._header.initial.restore_time == 0 or None
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'building' and obj.object_type == 'tc_1':
                    return False
        return nomad

    def is_regicide(self):
        """Is this game regicide?"""
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'unit' and obj.object_type == 'king':
                    return True
        return False

    def is_arena(self):
        """Is this game arena?

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

    def _parse_player(self, index, attributes, achievements, game_type):
        """Parse a player."""
        try:
            voobly_user = voobly.user(self._voobly_session, attributes.player_name, ladder_ids=VOOBLY_LADDERS.values())
            voobly_ladder = '{} {}'.format(game_type, self._diplomacy['type'])
            voobly_rating = voobly_user['ladders'].get(VOOBLY_LADDERS.get(voobly_ladder)).get('rating')
        except voobly.VooblyError:
            voobly_user = None
            voobly_rating = None
        return {
            'index': index,
            'number': attributes.player_color + 1,
            'color': mgz.const.PLAYER_COLORS[attributes.player_color],
            'name': attributes.player_name,
            'civilization': mgz.const.CIVILIZATION_NAMES[attributes.civilization],
            'position': self._compass_position(attributes.camera_x, attributes.camera_y),
            'score': achievements.total_score,
            'mvp': achievements.mvp,
            'winner': achievements.victory,
            'research': self._research.get(index),
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
                'feudal': achievements.technology.feudal_time,
                'castle': achievements.technology.castle_time,
                'imperial': achievements.technology.imperial_time
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
        map_dim = self._map.x
        third = map_dim * (1/3.0)
        for direction in mgz.const.COMPASS:
            point = mgz.const.COMPASS[direction]
            xl = point[0] * map_dim
            xu = (point[0] * map_dim) + third
            yl = point[1] * map_dim
            yu = (point[1] * map_dim) + third
            if player_x >= xl and player_x < xu and player_y >= yl and player_y < yu:
                return direction

    def _players(self):
        """Get player attributes with index. No Gaia."""
        for i in range(1, self._header.replay.num_players):
            yield i, self._header.initial.players[i].attributes

    def players(self, achievements, game_type):
        """Return parsed players."""
        for i, attributes in self._players():
            yield self._parse_player(i, attributes, achievements[i - 1], game_type)

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
                teams[team] = []
            teams[team].append(attributes.player_color + 1)
        return list(teams.values())

    def _compute_diplomacy(self):
        """Compute diplomacy."""
        self._diplomacy = {
            'teams': self.teams(),
            'ffa': len(self.teams()) == self._player_num + self._computer_num and self._player_num + self._computer_num > 2,
            'team_game':  len(self.teams()) == 2 and self._player_num + self._computer_num > 2,
            '1v1': self._player_num + self._computer_num == 2,
        }
        self._diplomacy['type'] = self._diplomacy_type(self._diplomacy)

    def _diplomacy_type(self, diplomacy):
        """Compute diplomacy type."""
        if diplomacy['ffa']: return 'ffa'
        if diplomacy['team_game']: return 'team_game'
        if diplomacy['1v1']: return '1v1'

    def _won_in(self, summary):
        """Get age the game was won in."""
        if not summary['finished']:
            return
        starting_age = summary['settings']['starting_age'].lower()
        if starting_age == 'post imperial':
            starting_age = 'imperial'
        ages_reached = set([starting_age])
        for player in summary['players']:
            for age, reached in player['ages'].items():
                if reached:
                    ages_reached.add(age)
        ages = ['imperial', 'castle', 'feudal', 'dark']
        for age in ages:
            if age in ages_reached:
                return age

    def _summarize(self, postgame):
        """Game summary implementation."""
        self._achievements_summarized = True
        data = postgame.action
        game_type = 'DM' if data.is_deathmatch else 'RM'
        self._summary = {
            'chat': self._chat,
            'players': list(self.players(data.achievements, game_type)),
            'diplomacy': self._diplomacy,
            'rec_owner_number': self._header.initial.players[self._header.replay.rec_player].attributes.player_color + 1,
            'settings': {
                'type': game_type,
                'difficulty': self._header.scenario.game_settings.difficulty,
                'resource_level': data.resource_level,
                'population_limit': self._header.lobby.population_limit * 25,
                'speed': self._header.replay.game_speed,
                'reveal_map': data.reveal_map,
                'starting_age': data.starting_age.title() if data.starting_age not in ['postimperial', 'dmpostimperial'] else 'Post Imperial',
                'victory_condition': data.victory_type,
                'team_together': data.team_together,
                'all_technologies': data.all_techs,
                'cheats': data.cheats,
                'lock_teams': data.lock_teams,
                'lock_speed': data.lock_speed,
                'record_game': True
            },
            'map': {
                'name': self._map.name(),
                'size': self._map.size(),
                'nomad': self.is_nomad(),
                'regicide': self.is_regicide(),
                'arena': self.is_arena()
            },
            'restore': {
                'restored': self._header.initial.restore_time > 0,
                'start_time': mgz.util.convert_to_timestamp(self._header.initial.restore_time / 1000)
            },
            'voobly': {
                'ladder': self._ladder,
                'rated': self._ladder != None
            },
            'number_of_humans': data.player_num,
            'number_of_ai': data.computer_num,
            'duration': data.duration,
            'finished': data.complete,
            'file': {
                'version': mgz.const.VERSIONS[self._header.version],
                'filename': os.path.basename(self._path),
                'timestamp': datetime.datetime.fromtimestamp(os.path.getmtime(self._path)).strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        self._summary['diplomacy']['type'] = self._diplomacy_type(self._summary['diplomacy'])
        self._summary['won_in'] = self._won_in(self._summary).title()
