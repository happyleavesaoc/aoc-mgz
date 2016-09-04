import mgz
import mgz.body
import mgz.util
import mgz.const


class ChatMessage():
    def __init__(self, structure):
        self._text = structure.data.text

    def __repr__(self):
        return self._text


class Sync():
    def __init__(self, structure):
        self._view = structure.view

    def __repr__(self):
        return ','.join([str(self._view.x), str(self._view.y)])


class Action():
    def __init__(self, structure):
        self._type = structure.action.type

    def __repr__(self):
        return self._type


class Map():
    def __init__(self, map_id, x, y, instructions):
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
        return self._name

    def size(self):
        return self._size

    def __repr__(self):
        return self._name


class RecordedGame():
    def __init__(self, path):
        self._handle = open(path, 'rb')
        self._handle.seek(0, 2)
        self._eof = self._handle.tell()
        self._handle.seek(0)
        self._header = mgz.header.parse_stream(self._handle)
        self._body_position = self._handle.tell()
        self._time = 0
        self._achievements_summarized = False
        self._ladder = None
        self._map = Map(self._header.scenario.game_settings.map_id, self._header.map_info.size_x, self._header.map_info.size_y, self._header.scenario.messages.instructions)

    def operations(self, op_types=None):
        if not op_types:
            op_types = ['message', 'action', 'sync', 'savedchapter']
        while self._handle.tell() < self._eof:
            operation = mgz.body.operation.parse_stream(self._handle)
            if operation.type == 'sync':
                self._time += operation.time_increment
            if operation.type == 'action' and operation.action.type == 'postgame':
                self._summarize(operation)
            if operation.type not in op_types:
                continue
            if operation.type == 'sync':
                yield Sync(operation)
            elif operation.type == 'action' and operation.action.type != 'postgame':
                yield Action(operation)
            elif operation.type == 'message' and operation.subtype == 'chat':
                self._parse_chat(operation)
                yield ChatMessage(operation), mgz.util.convert_to_timestamp(self._time / 1000)

    def reset(self):
        self._time = 0
        self._handle.seek(self._body_position)

    def summarize(self):
        if not self._achievements_summarized:
            for _ in self.operations(): pass
        return self._summary

    def is_nomad(self):
        nomad =  self._header.initial.restore_time == 0 or 'unknown'
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'building' and obj.object_type == 'tc_1':
                        return False

    def is_regicide(self):
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'unit' and obj.object_type == 'king':
                    return True
        return False

    def is_arena(self):
        for i in range(1, self._header.replay.num_players):
            for obj in self._header.initial.players[i].objects:
                if obj.type == 'building' and obj.object_type == 'stone_wall':
                    return True
        return False

    def _parse_chat(self, operation):
        line = operation.data.text
        if line.find('Voobly: Ratings provided') > 0:
            start = line.find("'") + 1
            end = line.find("'", start)
            self._ladder = line[start:end]

    def _parse_player(self, attributes, achievements):
        return {
            'number': attributes.player_color + 1,
            'color': mgz.const.PLAYER_COLORS[attributes.player_color],
            'name': attributes.player_name,
            'civilization': mgz.const.CIVILIZATION_NAMES[attributes.civilization],
            'position': self._compass_position(attributes.camera_x, attributes.camera_y),
            'score': achievements.total_score,
            'winner': achievements.victory == 1
        }

    def _compass_position(self, player_x, player_y):
        map_dim = self._map.x
        third = map_dim * (1/3.0)
        for direction in mgz.const.COMPASS.keys():
            point = mgz.const.COMPASS[direction]
            xl = point[0] * map_dim
            xu = (point[0] * map_dim) + third
            yl = point[1] * map_dim
            yu = (point[1] * map_dim) + third
            if player_x >= xl and player_x < xu and player_y >= yl and player_y < yu:
                return direction

    def players(self, achievements):
        for i in range(1, self._header.replay.num_players):
            yield self._parse_player(self._header.initial.players[i].attributes, achievements[i - 1])

    def teams(self):
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
        return teams.values()

    def _summarize(self, postgame):
        self._achievements_summarized = True
        data = postgame.action
        self._summary = {
            'players': list(self.players(data.achievements)),
            'diplomacy': {
                'teams': self.teams(),
                'ffa': len(self.teams()) == data.player_num + data.computer_num and data.player_num + data.computer_num > 2,
                'team_game':  len(self.teams()) == 2 and data.player_num + data.computer_num > 2,
                '1v1': data.player_num + data.computer_num == 2
            },
            'rec_owner_number': self._header.initial.players[self._header.replay.rec_player].attributes.player_color + 1,
            'settings': {
                'type': self._header.lobby.game_type,
                'difficulty': self._header.scenario.game_settings.difficulty,
                'resource_level': data.resource_level,
                'population_limit': self._header.lobby.population_limit * 25,
                'speed': self._header.replay.game_speed,
                'reveal_map': data.reveal_map,
                'starting_age': data.starting_age,
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
            'finished': data.complete
        }
