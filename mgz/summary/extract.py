""""Extract data via playback."""

import logging
from collections import defaultdict

from mgz.playback import Client, Source
from mgz.summary.chat import parse_chat


LOGGER = logging.getLogger(__name__)


def get_lobby_chat(header, encoding, diplomacy_type, players):
    """Get lobby chat."""
    chats = []
    for message in header.lobby.messages:
        if not message.message:
            continue
        try:
            chat = parse_chat(
                message.message.decode(encoding), 0, players, diplomacy_type, origination='lobby'
            )
            chats.append(chat)
        except UnicodeDecodeError:
            LOGGER.warning('could not decode lobby chat')
    return chats


async def get_extracted_data( # pylint: disable=too-many-arguments, too-many-locals
        header, encoding, diplomacy_type, players, start_time, duration, playback, handle
):
    """Get extracted data."""
    timeseries = []
    research = defaultdict(dict)
    market = []
    objects = {}
    chats = get_lobby_chat(header, encoding, diplomacy_type, players)
    client = await Client.create(playback, handle.name, start_time, duration)

    async for tick, source, message in client.sync(timeout=120):
        if source == Source.MGZ and message[0] == 4:
            try:
                chats.append(parse_chat(
                    message[1].decode(encoding), tick, players, diplomacy_type
                ))
            except UnicodeDecodeError:
                LOGGER.warning('could not decode chat')

        elif source == Source.MEMORY:
            market.append({
                'timestamp': tick,
                'food': message.MarketCoefficients().Food(),
                'wood': message.MarketCoefficients().Wood(),
                'stone': message.MarketCoefficients().Stone()
            })

            for i in range(0, message.ObjectsLength()):
                obj = message.Objects(i)
                if obj.OwnerId() == 0:
                    continue
                if obj.Id() not in objects and obj.State() == 2:
                    objects[obj.Id()] = {
                        'player_number': obj.OwnerId(),
                        'created': tick,
                        'object_id': obj.MasterObjectId(),
                        'destroyed': None,
                        'destroyed_by_player_number': None,
                        'destroyed_by_instance_id': None,
                        'deleted': False
                    }
                elif obj.State() == 4 and obj.Id() in objects:
                    data = {
                        'destroyed': tick
                    }
                    """
                    data = {}
                    if obj.KilledByPlayerId() == -1:
                        data = {
                            'destroyed': tick,
                            'deleted': True
                        }
                    elif obj.KilledByUnitId() in objects:
                        data = {
                            'destroyed': tick,
                            'destroyed_by_player_number': obj.KilledByPlayerId(),
                            'destroyed_by_instance_id': obj.KilledByUnitId()
                        }
                    """
                    objects[obj.Id()].update(data)

            for i in range(0, message.PlayersLength()):
                player = message.Players(i)
                timeseries.append({
                    'timestamp': tick,
                    'player_number': player.Id(),
                    'population': player.Population(),
                    'military': player.MilitaryPopulation(),
                    'percent_explored': player.PercentMapExplored(),
                    'headroom': int(player.Headroom()),
                    'food': int(player.Food()),
                    'wood': int(player.Wood()),
                    'stone': int(player.Stone()),
                    'gold': int(player.Gold())
                })

                for j in range(0, player.TechsLength()):
                    tech = player.Techs(j)
                    if tech.State() == 3 and tech.IdIndex() not in research[player.Id()]:
                        research[player.Id()][tech.IdIndex()] = {'started': tick, 'finished': None}
                    elif tech.State() == 4 and tech.IdIndex() in research[player.Id()]:
                        research[player.Id()][tech.IdIndex()]['finished'] = tick
                    elif tech.State() == 2 and tech.IdIndex() in research[player.Id()]:
                        del research[player.Id()][tech.IdIndex()]

    r = []
    for pid, techs in research.items():
        for tid, values in techs.items():
            r.append(dict(values, player_number=pid, technology_id=tid))
    o = [dict(values, instance_id=oid) for oid, values in objects.items()]
    handle.close()
    return {
        'chat': chats,
        'timeseries': timeseries,
        'research': r,
        'market': market,
        'objects': o
    }
