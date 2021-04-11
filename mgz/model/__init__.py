"""Convert parsed data into object-oriented model."""

import codecs
from datetime import timedelta

from mgz import fast
from mgz.reference import get_consts, get_dataset
from mgz.fast.header import parse
from mgz.model.definitions import *
from mgz.summary.chat import parse_chat, Chat as ChatEnum
from mgz.summary.diplomacy import get_diplomacy_type
from mgz.summary.map import get_map_data
from mgz.summary.objects import TC_IDS


def parse_match(handle):
    """Parse a match.

    This is one big function because the dependency graph between
    the variables is dense.
    """

    data = parse(handle)
    consts = get_consts()

    dataset_id, dataset = get_dataset(data['version'], data['mod'])
    map_data, encoding, language = get_map_data(
        data['scenario']['map_id'],
        data['scenario']['instructions'],
        data['map']['dimension'],
        data['version'],
        dataset_id,
        dataset,
        data['map']['tiles'],
        de_seed=data['lobby']['seed']
    )

    # Handle DE-specific data
    if data['de']:
        de_players = {player['number']: player for player in data['de']['players']}
        lobby = data['de']['lobby']
        guid = data['de']['guid']
    else:
        de_players = dict()
        lobby = None
        guid = None

    # Parse gaia objects
    gaia = [
        Object(
            dataset['objects'].get(str(obj['object_id'])),
            obj['instance_id'],
            Position(obj['position']['x'], obj['position']['y'])
        )
        for obj in data['players'][0]['objects']
    ]

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
            player['color_id'] + 1,
            player['name'].decode(encoding),
            consts['player_colors'][str(player['color_id'])],
            dataset['civilizations'][str(player['civilization_id'])]['name'],
            Position(pos_x, pos_y),
            [
                Object(
                    dataset['objects'].get(str(obj['object_id'])),
                    obj['instance_id'],
                    Position(obj['position']['x'], obj['position']['y'])
                )
                for obj in player['objects']
            ],
            player.get('profile_id')
        )

    # Assign teams
    team_ids = set([frozenset(s) for s in allies.values()])
    teams = []
    for team in team_ids:
        t = [players[x] for x in team]
        for x in team:
            players[x].team = t
        teams.append(t)

    # Compute diplomacy
    diplomacy_type = get_diplomacy_type(teams, players)

    # Extract lobby chat
    pd = [dict(name=p.name, number=n) for n, p in players.items()]
    chats = []
    for c in data['lobby']['chat']:
        chat = parse_chat(c, encoding, 0, pd, diplomacy_type, 'lobby')
        if chat['player_number'] not in players:
            continue
        chats.append(Chat(
            timedelta(milliseconds=chat['timestamp']),
            chat['message'],
            players[chat['player_number']]
        ))

    # Parse player actions
    fast.meta(handle)
    timestamp = 0
    resigned = []
    actions = []
    viewlocks = []
    last_viewlock = None
    while True:
        try:
            op_type, op_data = fast.operation(handle)
            if op_type is fast.Operation.SYNC:
                timestamp += op_data[0]
            elif op_type is fast.Operation.VIEWLOCK:
                if op_data == last_viewlock:
                    continue
                viewlocks.append(Viewlock(timedelta(milliseconds=timestamp), Position(*op_data)))
                last_viewlock = op_data
            elif op_type is fast.Operation.CHAT:
                chat = parse_chat(op_data, encoding, timestamp, pd, diplomacy_type, 'game')
                if chat['type'] == ChatEnum.MESSAGE:
                    chats.append(Chat(
                        timedelta(milliseconds=chat['timestamp']),
                        chat['message'],
                        players[chat['player_number']]
                    ))
            elif op_type is fast.Operation.ACTION:
                action_type, action_data = op_data
                action = Action(timedelta(milliseconds=timestamp), action_type)
                for key, value in action_data.items():
                    setattr(action, key, value)
                if 'player_id' in action_data:
                    action.player = players[action_data['player_id']]
                if 'technology_id' in action_data:
                    action.technology = dataset['technologies'][str(action_data['technology_id'])]
                if 'formation_id' in action_data:
                    action.formation = consts['formations'][str(action_data['formation_id'])]
                if 'building_id' in action_data:
                    action.building = dataset['objects'][str(action_data['building_id'])]
                if 'x' in action_data and 'y' in action_data:
                    action.position = Position(action_data['x'], action_data['y'])
                if action_type is fast.Action.RESIGN:
                    resigned.append(players[action_data['player_id']])
                actions.append(action)
        except EOFError:
            break

    # Compute winner(s)
    for team in teams:
        winner = not any([player for player in team if player in resigned])
        for player in team:
            player.winner = winner

    return Match(
        list(players.values()),
        teams,
        gaia,
        Map(
            map_data['name'],
            map_data['dimension'],
            consts['map_sizes'][str(map_data['dimension'])],
            map_data['custom'],
            map_data['seed'],
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
            players[data['metadata']['owner_id']],
            viewlocks
        ),
        consts['speeds'][str(int(round(data['metadata']['speed'], 2) * 100))],
        data['metadata']['cheats'],
        data['lobby']['lock_teams'],
        data['lobby']['population'],
        chats,
        guid,
        lobby,
        dataset['dataset']['name'],
        consts['game_types'][str(data['lobby']['game_type_id'])],
        consts['map_reveal_choices'][str(data['lobby']['reveal_map_id'])],
        timedelta(milliseconds=timestamp),
        diplomacy_type,
        data['version'],
        actions
    )
