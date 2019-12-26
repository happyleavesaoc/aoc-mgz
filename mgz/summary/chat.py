"""Chat Messages."""


def parse_chat(line, timestamp, players, diplomacy_type=None, origination='game'):
    """Initalize."""
    data = {
        'timestamp': timestamp,
        'origination': origination
    }
    if line.find('Voobly: Ratings provided') > 0:
        _parse_ladder(data, line)
    elif line.find('Voobly') == 3:
        _parse_voobly(data, line)
    elif line.find('<Rating>') > 0:
        _parse_rating(data, line)
    elif line.find('@#0<') == 0:
        _parse_injected(data, line)
    else:
        _parse_chat(data, line, players, diplomacy_type)
    return data


def _parse_ladder(data, line):
    start = line.find("'") + 1
    end = line.find("'", start)
    data.update({
        'type': 'ladder',
        'ladder': line[start:end]
    })


def _parse_voobly(data, line):
    message = line[11:]
    data.update({
        'type': 'voobly',
        'message': message
    })


def _parse_rating(data, line):
    player_start = line.find('>') + 2
    player_end = line.find(':', player_start)
    player = line[player_start:player_end]
    rating = int(line[player_end + 2:len(line)])
    data.update({
        'type': 'rating',
        'player': player,
        'rating': rating
    })

def _parse_injected(data, line):
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
        'type': 'injected',
        'origination': origination.lower(),
        'name': name,
        'message': '{}{}'.format(prefix, message)
    })


def _parse_chat(data, line, players, diplomacy_type):
    player_start = line.find('#') + 2
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
        if player_h['name'] == player:
            number = player_h['number']
    data.update({
        'type': 'chat',
        'player_number': number,
        'message': message.strip(),
        'audience': group.lower()
    })
