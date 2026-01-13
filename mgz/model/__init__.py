"""Convert parsed data into object-oriented model."""

import codecs
import collections
import _hashlib
import hashlib
from datetime import timedelta, datetime
from enum import Enum

import dataclasses

from mgz import fast
from mgz.reference import get_consts, get_dataset
from mgz.fast import Action as ActionEnum
from mgz.fast.header import parse
from mgz.model.definitions import *
from mgz.model.inputs import Inputs
from mgz.common.chat import parse_chat, Chat as ChatEnum
from mgz.common.diplomacy import get_diplomacy_type
from mgz.common.map import get_map_data
from mgz.util import Version


TC_IDS = [71, 109, 141, 142]
AI_ACTIONS = [ActionEnum.AI_ORDER]


def enrich_action(action, action_data, dataset, consts):
    """Enrich action data with lookups."""
    if 'x' in action_data and 'y' in action_data and action_data['x'] >=0 and action_data['y'] >= 0:
        if action.type != fast.Action.SPECIAL or ('target_id' in action_data and action_data['target_id'] > 0):
            action.position = Position(action_data['x'], action_data['y'])
            del action.payload['x']
            del action.payload['y']
    if 'technology_id' in action_data:
        action.payload['technology'] = dataset['technologies'].get(str(action_data['technology_id']))
    if 'formation_id' in action_data:
        action.payload['formation'] = consts['formations'].get(str(action_data['formation_id']))
    if 'stance_id' in action_data:
        action.payload['stance'] = consts['stances'].get(str(action_data['stance_id']))
    if 'building_id' in action_data:
        action.payload['building'] = dataset['objects'].get(str(action_data['building_id']))
    if 'unit_id' in action_data:
        action.payload['unit'] = dataset['objects'].get(str(action_data['unit_id']))
    if 'command_id' in action_data:
        action.payload['command'] = consts['commands'].get(str(action_data['command_id']))
    if 'order_id' in action_data:
        action.payload['order'] = consts['orders'].get(str(action_data['order_id']))
    if 'resource_id' in action_data:
        action.payload['resource'] = consts['resources'].get(str(action_data['resource_id']))


def get_difficulty(data):
    if data['version'] is Version.HD:
        return data['hd']['difficulty_id']
    elif data['version'] is Version.DE:
        return data['de']['difficulty_id']
    return data['scenario']['difficulty_id']


def get_team_together(data):
    if data['version'] is Version.DE:
        return data['de']['team_together']
    return None


def get_lock_speed(data):
    if data['version'] is Version.DE:
        return data['de']['lock_speed']
    return None


def get_all_technologies(data):
    if data['version'] is Version.DE:
        return data['de']['all_technologies']
    return None

def get_starting_age(data):
    if data['version'] is Version.DE:
        return data['de']['starting_age_id']
    return None


def get_map_id(data):
    if data['version'] is Version.HD:
        return data['hd']['map_id']
    if data['version'] is Version.DE:
        return data['de']['rms_map_id']
    return data['scenario']['map_id']


def get_hash(data):
    if data['version'] is Version.DE:
        return data['de']['hash']
    return None


def parse_match(handle):
    """Parse a match.

    This is one big function because the dependency graph between
    the variables is dense.
    """

    data = parse(handle)
    body_pos = handle.tell() - 4 # log version
    consts = get_consts()

    dataset_id, dataset = get_dataset(data['version'], data['mod'])
    map_id = get_map_id(data)
    try:
            map_data, encoding, language = get_map_data(
            map_id,
            data['scenario']['instructions'],
            data['map']['dimension'],
            data['version'],
            dataset_id,
            dataset,
            data['map']['tiles'],
            de_seed=data['lobby']['seed']
        )
    except ValueError as e:
        raise RuntimeError(f"could not get map data: {e}")

    # Handle DE-specific data
    rated = None
    if data['de']:
        de_players = {player['number']: player for player in data['de']['players']}
        lobby = data['de']['lobby']
        guid = data['de']['guid']
        rated = data['de']['rated']
    else:
        de_players = dict()
        lobby = None
        guid = None

    # Parse gaia objects
    gaia = [
        Object(
            dataset['objects'].get(str(obj['object_id'])),
            obj['class_id'],
            obj['object_id'],
            obj['instance_id'],
            obj['index'],
            Position(obj['position']['x'], obj['position']['y'])
        )
        for obj in data['players'][0]['objects']
    ]

    inputs = Inputs({o.instance_id:o.name for o in gaia})

    # Parse players
    players = dict()
    allies = dict()
    for player in data['players'][1:]:
        allies[player['number']] = set([player['number']])
        for i, stance in enumerate(player['diplomacy']):
            if stance == 2:
                allies[player['number']].add(i)
        de_player = de_players.get(player['number'])
        if de_player:
            player.update(de_player)
        pos_x = None
        pos_y = None
        for obj in player['objects']:
            if obj['object_id'] in TC_IDS:
                pos_x = obj['position']['x']
                pos_y = obj['position']['y']
        players[player['number']] = Player(
            player['number'],
            player['name'].decode(encoding),
            consts['player_colors'][str(player['color_id'])],
            player['color_id'],
            dataset['civilizations'][str(player['civilization_id'])]['name'],
            player['civilization_id'],
            Position(pos_x, pos_y),
            [
                Object(
                    dataset['objects'].get(str(obj['object_id'])),
                    obj['class_id'],
                    obj['object_id'],
                    obj['instance_id'],
                    obj['index'],
                    Position(obj['position']['x'], obj['position']['y'])
                )
                for obj in player['objects']
            ],
            player.get('profile_id'),
            [],
            player.get('prefer_random'),
        )

    # Assign teams
    if de_players:
        by_team = collections.defaultdict(list)
        for number, player in de_players.items():
            if player['team_id'] > 1:
                by_team[player['team_id']].append(number)
            elif player['team_id'] == 1:
                by_team[number + 9].append(number)
        team_ids = by_team.values()
    else:
        team_ids = set([frozenset(s) for s in allies.values()])
    teams = []
    for team in team_ids:
        t = [players[x] for x in team]
        for x in team:
            players[x].team = t
            players[x].team_id = team
        teams.append(t)

    # Compute diplomacy
    diplomacy_type = get_diplomacy_type(teams, players)

    # Extract lobby chat
    pd = [dict(name=p.name, number=n) for n, p in players.items()]
    chats = []
    for c in data['lobby']['chat']:
        chat = parse_chat(c, encoding, 0, pd, diplomacy_type, 'lobby')
        if chat['type'] == ChatEnum.DISCARD or chat['player_number'] not in players:
            continue
        chats.append(Chat(
            timedelta(milliseconds=chat['timestamp']),
            chat['message'],
            chat['origination'],
            chat['audience'],
            players[chat['player_number']]
        ))
        inputs.add_chat(chats[-1])

    # Parse player actions
    fast.meta(handle)
    timestamp = 0
    resigned = []
    actions = []
    viewlocks = []
    uptimes = []
    eapm = collections.Counter()
    last_viewlock = None
    while True:
        try:
            op_type, op_data = fast.operation(handle)
            if op_type is fast.Operation.SYNC:
                timestamp += op_data[0]
                if op_data[2]:
                    stat_row = op_data[2]
                    for player in players.values():
                        if player.number not in stat_row:
                            continue
                        stats = stat_row[player.number]
                        player.timeseries.append(TimeseriesRow(
                            timestamp=timedelta(milliseconds=stat_row['current_time']),
                            total_resources=stats['total_res'],
                            total_objects=stats['obj_count']
                        ))
            elif op_type is fast.Operation.VIEWLOCK:
                if op_data == last_viewlock:
                    continue
                viewlock = Viewlock(timedelta(milliseconds=timestamp), Position(*op_data), players[data['metadata']['owner_id']])
                viewlocks.append(viewlock)
                last_viewlock = op_data
            elif op_type is fast.Operation.CHAT:
                chat = parse_chat(op_data, encoding, timestamp, pd, diplomacy_type, 'game')
                if chat['type'] == ChatEnum.MESSAGE:
                    chats.append(Chat(
                        timedelta(milliseconds=chat['timestamp'] + data['map']['restore_time']),
                        chat['message'],
                        chat['origination'],
                        chat['audience'],
                        players[chat['player_number']]
                    ))
                    inputs.add_chat(chats[-1])
                if chat['type'] == ChatEnum.AGE:
                    uptimes.append(
                        Uptime(
                            timedelta(milliseconds=chat['timestamp'] + data['map']['restore_time']),
                            chat['age'],
                            players.get(chat['player_number']),
                        )
                    )
            elif op_type is fast.Operation.ACTION:
                action_type, action_data = op_data
                action = Action(timedelta(milliseconds=timestamp), action_type, action_data)
                if action_type is fast.Action.RESIGN and action_data['player_id'] in players:
                    resigned.append(players[action_data['player_id']])
                if 'player_id' in action_data and action_data['player_id'] in players:
                    if action_type not in AI_ACTIONS:
                        eapm[action_data['player_id']] += 1
                    action.player = players[action_data['player_id']]
                    del action.payload['player_id']
                enrich_action(action, action_data, dataset, consts)
                actions.append(action)
                inputs.add_action(action)
            elif op_type is fast.Operation.POSTGAME and "leaderboards" in op_data:
                by_number = {x["number"]: x["rating"] for x in op_data["leaderboards"][0]["players"]}
                for player in players.values():
                    player.rate_snapshot = by_number.get(player.number - 1)
        except EOFError:
            break

    # Compute winner(s)
    for team in teams:
        winner = not any([player for player in team if player in resigned])
        if resigned:
            for player in team:
                player.winner = winner

    # Compute eAPM
    for player_id, action_count in eapm.items():
        players[player_id].eapm = int(round(eapm[player_id] / ((timestamp/1000)/60)))

    handle.seek(body_pos)
    file_bytes = handle.read()
    file_size = body_pos + 4 + len(file_bytes)
    file_hash = hashlib.sha1(file_bytes).hexdigest()
    return Match(
        list(players.values()),
        teams,
        gaia,
        Map(
            map_id,
            map_data['name'],
            map_data['dimension'],
            consts['map_sizes'].get(str(map_data['dimension'])),
            map_data['custom'],
            map_data['seed'],
            data['de']['rms_mod_id'] if data['version'] is Version.DE and map_data['custom'] else None,
            map_data['name'].startswith('ZR@'),
            map_data['modes'],
            [
                Tile(
                    tile['terrain_id'],
                    tile['elevation'],
                    Position(tile['x'], tile['y'])
                ) for tile in map_data['tiles']
            ]
        ),
        File(
            codecs.lookup(encoding),
            language,
            file_hash,
            file_size,
            data['device'],
            players[data['metadata']['owner_id']],
            viewlocks
        ),
        data['map']['restore_time'] > 0,
        timedelta(milliseconds=data['map']['restore_time']),
        consts['speeds'][str(int(round(data['metadata']['speed'], 2) * 100))],
        int(round(data['metadata']['speed'], 2) * 100),
        data['metadata']['cheats'],
        data['lobby']['lock_teams'],
        data['lobby']['population'],
        chats,
        guid,
        lobby,
        rated,
        dataset['dataset']['name'],
        consts['game_types'][str(data['lobby']['game_type_id'])],
        data['lobby']['game_type_id'],
        consts['map_reveal_choices'][str(data['lobby']['reveal_map_id'])],
        data['lobby']['reveal_map_id'],
        consts['difficulties'].get(str(get_difficulty(data))),
        get_difficulty(data),
        consts['starting_ages'].get(str(get_starting_age(data))),
        get_starting_age(data),
        get_team_together(data),
        get_lock_speed(data),
        get_all_technologies(data),
        True if data['version'] is Version.DE else None,
        timedelta(milliseconds=timestamp + data['map']['restore_time']),
        diplomacy_type,
        bool(resigned),
        dataset_id,
        data['version'],
        data['game_version'],
        data['save_version'],
        data['log_version'],
        data['de']['build'] if data['version'] is Version.DE else None,
        datetime.fromtimestamp(data['de']['timestamp']) if data['version'] is Version.DE and data['de']['timestamp'] else None,
        timedelta(seconds=data['de']['spec_delay']) if data['version'] is Version.DE else None,
        data['de']['allow_specs'] if data['version'] is Version.DE else None,
        data['de']['hidden_civs'] if data['version'] is Version.DE else None,
        data['de']['visibility_id'] == 2 if data['version'] is Version.DE else None,
        get_hash(data),
        actions,
        inputs.inputs,
        uptimes
    )


def serialize(obj):
    """Serialize model.

    Returns a nested datastructure with no circular references,
    appropriate for dumping to JSON, YAML, etc.
    """
    seen = set()

    def impl(obj):
        """Recursive serialization implementation."""
        if dataclasses.is_dataclass(obj) and isinstance(obj, collections.abc.Hashable):
            if obj in seen:
                return hash(obj)
            seen.add(obj)
        if type(obj) is list:
            return [v for v in [impl(o) for o in obj] if v is not None]
        elif type(obj) is dict:
            return {k:v for k, v in {f:impl(d) for f, d in obj.items()}.items() if v is not None}
        elif dataclasses.is_dataclass(obj):
            return {k:v for k, v in {f.name:impl(getattr(obj, f.name)) for f in dataclasses.fields(obj)}.items() if v is not None}
        elif isinstance(obj, (codecs.CodecInfo, Enum)):
            return obj.name
        elif isinstance(obj, timedelta):
            return str(obj)
        elif isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj, bytes):
            return None
        elif isinstance(obj, _hashlib.HASH):
            return obj.hexdigest()
        else:
            return obj

    return impl(obj)
