"""Chat Messages."""
import json
import logging
from enum import Enum

LOGGER = logging.getLogger(__name__)
AGE_MARKERS = [
    'advanced to the',
    'a progressé vers',
    '升级至',
    'avanzó a la',
    'đã phát triển lên',
    '시대로 발전했습니다',
    'vorangeschritten',
    'переход в',
    'avançou para a Idade',
    'wkroczyło w Erę',
    '升級至',
    'passaggio',
    'geÃ§ti',
    '進化し'
]
SAVE_MARKERS = [
    'Continuar con la partida en vez de guardar y salir',
    'Voto iniciado para guardar y salir del juego',
    'Chose to continue the game instead of save and exit',
    'Initiated vote to save and exit the game',
    'Vyber pokračovat ve hře místo ulo',
    'Escolha para continuar o jogo em vez de salvá-lo e fechá-lo',
    'Выберете Продолжить Игру вместо Сохранить и Выйти.',
    'Choisir pour continuer la partie au lieu d\'enregistrer et quitter.'
]


class Chat(Enum):
    """Chat types."""
    LADDER = 0
    VOOBLY = 1
    RATING = 2
    INJECTED = 3
    AGE = 4
    SAVE = 5
    MESSAGE = 6
    HELP = 7
    DISCARD = 8


def get_lobby_chat(header, encoding, diplomacy_type, players):
    """Get lobby chat."""
    chats = []
    if not hasattr(header.lobby, 'messages'):
        return chats
    for message in header.lobby.messages:
        if not message.message:
            continue
        try:
            chats.append(parse_chat(
                message.message, encoding, 0, players, diplomacy_type, origination='lobby'
            ))
        except UnicodeDecodeError:
            LOGGER.warning('could not decode lobby chat')
    return chats


def parse_chat(line, encoding, timestamp, players, diplomacy_type=None, origination='game'):
    """Initalize."""
    data = {
        'timestamp': timestamp,
        'origination': origination
    }
    try:
        line = line.strip(b'\x00').decode(encoding)
    except UnicodeDecodeError:
        data['type'] = Chat.DISCARD
        return data
    for save_marker in SAVE_MARKERS:
        if line.find(save_marker) > 0:
            data['type'] = Chat.SAVE
            return data
    for age_marker in AGE_MARKERS:
        if line.find(age_marker) > 0:
            data['type'] = Chat.AGE
            return data
    if line.find('Voobly: Ratings provided') > 0:
        _parse_ladder(data, line)
    elif line.find('Voobly') == 3:
        _parse_voobly(data, line)
    elif line.find('<Rating>') > 0:
        _parse_rating(data, line)
    elif line.find('@#0<') == 0:
        _parse_injected(data, line)
    elif line.find('--') == 3:
        _parse_help(data, line)
    elif line.startswith('{"'):
        _parse_json(data, line, diplomacy_type)
    else:
        _parse_chat(data, line, players, diplomacy_type)
    if not _validate(data, players):
        data['type'] = Chat.DISCARD
    return data


def _validate(data, players):
    """Chat messages can be bugged - check for invalid messages."""
    numbers = [p['number'] for p in players]
    if 'player_number' in data and data['player_number'] not in numbers:
        return False
    return True


def _parse_json(data, line, diplomacy_type):
    """Parse DE JSON chat."""
    payload = json.loads(line)
    if payload['messageAGP'] == '':
        # Use this condition to tell whether to ignore the chat. It might be from another game for example.
        data['type'] = Chat.DISCARD
        return

    audience = 'team'
    if payload['channel'] == 0:
        if diplomacy_type == '1v1':
            audience = 'all'
    elif payload['channel'] == 1:
        audience = 'all'
    data.update({
        'type': Chat.MESSAGE,
        'player_number': payload['player'],
        'message': payload['message'].strip(),
        'audience': audience
    })


def _parse_ladder(data, line):
    """Parse ladder from chat."""
    start = line.find("'") + 1
    end = line.find("'", start)
    data.update({
        'type': Chat.LADDER,
        'ladder': line[start:end]
    })


def _parse_voobly(data, line):
    """Parse voobly message from chat."""
    message = line[11:]
    data.update({
        'type': Chat.VOOBLY,
        'message': message
    })


def _parse_rating(data, line):
    """Parse rating from chat."""
    player_start = line.find('>') + 2
    player_end = line.find(':', player_start)
    player = line[player_start:player_end]
    rating = int(line[player_end + 2:len(line)])
    data.update({
        'type': Chat.RATING,
        'player': player,
        'rating': rating
    })


def _parse_injected(data, line):
    """Parse injected chat."""
    prefix = ''
    if line.find('<Team>') > 0:
        line = line.replace('<Team>', '', 1)
        prefix = ';'
    origination_start = line.find('<') + 1
    origination_end = line.find('>', origination_start)
    origination = line[origination_start:origination_end]
    name_end = line.find(':', origination_end)
    name = line[origination_end + 2:name_end]
    message = line[name_end + 2:]
    data.update({
        'type': Chat.INJECTED,
        'origination': origination.lower(),
        'name': name,
        'message': '{}{}'.format(prefix, message)
    })


def _parse_help(data, line):
    """Mark help-generated chat."""
    data['type'] = Chat.HELP


def _parse_chat(data, line, players, diplomacy_type):
    """Parse in-game chat message."""
    if not line or len(line) < 5:
        data['type'] = Chat.DISCARD
        return
    player_start = line.find('#') + 2
    if line[4] == ' ':
        player_start = line.find(' ') + 1
    player_end = line.find(':', player_start)
    player = line[player_start:player_end]
    if data['timestamp'] == 0:
        group = 'All'
    elif diplomacy_type == 'TG':
        group = 'Team'
    else:
        group = 'All'
    if player.find('>') > 0:
        group = player[1:player.find('>')]
        player = player[player.find('>') + 1:]
    if group.lower() in ['todos', 'всем', 'tous']:
        group = 'All'
    elif group.lower() in ['隊伍', 'squadra']:
        group = 'Team'
    message = line[player_end + 2:]
    number = None
    for player_h in players:
        if player_h['name'] in player:
            number = player_h['number']
    data.update({
        'type': Chat.MESSAGE,
        'player_number': number,
        'message': message.strip(),
        'audience': group.lower()
    })
