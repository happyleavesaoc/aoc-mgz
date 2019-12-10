"""Chat Messages."""

import mgz.const


# pylint: disable=too-few-public-methods
class ChatMessage():
    """Parse a chat message."""

    # pylint: disable=too-many-arguments
    def __init__(self, line, timestamp, players, diplomacy_type=None, origination='game'):
        """Initalize."""
        self.data = {
            'timestamp': timestamp,
            'origination': origination
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
        origination_start = line.find('<') + 1
        origination_end = line.find('>', origination_start)
        origination = line[origination_start:origination_end]
        name_end = line.find(':', origination_end)
        name = line[origination_end + 2:name_end]
        message = line[name_end + 2:]
        self.data.update({
            'type': 'injected',
            'origination': origination.lower(),
            'name': name,
            'message': '{}{}'.format(prefix, message)
        })

    def _parse_chat(self, line, players, diplomacy_type):
        player_start = line.find('#') + 2
        player_end = line.find(':', player_start)
        player = line[player_start:player_end]
        if self.data['timestamp'] == 0:
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
        color = None
        number = None
        for player_h in players:
            if player_h['name'] == player:
                color = mgz.const.PLAYER_COLORS[player_h['color_id']]
                number = player_h['number']
        self.data.update({
            'type': 'chat',
            'number': number,
            'message': message.strip(),
            'audience': group.lower()
        })

    def __repr__(self):
        """Printable representation."""
        if self.data['type'] == 'chat':
            return '{} <{}> {}: {}'.format(self.data['timestamp'], self.data['to'],
                                           self.data['player'], self.data['message'])
        elif self.data['type'] == 'rating':
            return '{}: {}'.format(self.data['player'], self.data['rating'])
        elif self.data['type'] == 'ladder':
            return 'Ladder: {}'.format(self.data['ladder'])
        elif self.data['type'] == 'injected':
            return '{} <{}> {}: {}'.format(self.data['timestamp'], self.data['origination'],
                                           self.data['name'], self.data['message'])
        elif self.data['type'] == 'voobly':
            return 'Voobly: {}'.format(self.data['message'])
