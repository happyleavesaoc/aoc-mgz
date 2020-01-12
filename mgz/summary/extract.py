""""Extract data via playback."""

import logging
from collections import defaultdict

from mgz.playback import Client, Source
from mgz.summary.chat import parse_chat
from mgz import fast


LOGGER = logging.getLogger(__name__)


def has_diff(data, **kwargs):
    """Simple dict subset diff."""
    for key, value in kwargs.items():
        if data.get(key) != value:
            return True
    return False


def get_lobby_chat(header, encoding, diplomacy_type, players):
    """Get lobby chat."""
    chats = []
    for message in header.lobby.messages:
        if not message.message:
            continue
        try:
            chats.append(parse_chat(
                message.message.decode(encoding), 0, players, diplomacy_type, origination='lobby'
            ))
        except UnicodeDecodeError:
            LOGGER.warning('could not decode lobby chat')
    return chats


def flatten_research(research):
    """Flatten research data."""
    flat = []
    for pid, techs in research.items():
        for tid, values in techs.items():
            flat.append(dict(values, player_number=pid, technology_id=tid))
    return flat


def build_timeseries_record(tick, player):
    """Build a timeseries record."""
    return {
        'timestamp': tick,
        'player_number': player.Id(),
        'population': player.Population(),
        'military': player.MilitaryPopulation(),
        'percent_explored': player.PercentMapExplored(),
        'headroom': int(player.Headroom()),
        'food': int(player.Food()),
        'wood': int(player.Wood()),
        'stone': int(player.Stone()),
        'gold': int(player.Gold()),
        'relics_captured': int(player.VictoryPoints().RelicsCaptured()),
        'relic_gold': int(player.VictoryPoints().RelicGold()),
        'trade_profit': int(player.VictoryPoints().TradeProfit()),
        'tribute_received': int(player.VictoryPoints().TributeReceived()),
        'tribute_sent': int(player.VictoryPoints().TributeSent()),
        'total_food': int(player.VictoryPoints().TotalFood()),
        'total_wood': int(player.VictoryPoints().TotalWood()),
        'total_gold': int(player.VictoryPoints().TotalGold()),
        'total_stone': int(player.VictoryPoints().TotalStone())
    }


def update_research(player_number, tech, research):
    """Update research structure."""
    if tech.State() == 3 and tech.IdIndex() not in research[player_number]:
        research[player_number][tech.IdIndex()] = {
            'started': tech.LastStateChange(),
            'finished': None
        }
    elif tech.State() == 4 and tech.IdIndex() in research[player_number]:
        research[player_number][tech.IdIndex()]['finished'] = tech.LastStateChange()
    elif tech.State() == 2 and tech.IdIndex() in research[player_number]:
        del research[player_number][tech.IdIndex()]


def update_market(tick, coefficients, market):
    """Update market coefficients structure."""
    last = None
    change = True
    food = coefficients.Food()
    wood = coefficients.Wood()
    stone = coefficients.Stone()
    if market:
        last = market[-1]
        change = has_diff(last, food=food, wood=wood, stone=stone)
    if change:
        market.append({
            'timestamp': tick,
            'food': food,
            'wood': wood,
            'stone': stone
        })

def update_objects(tick, obj, objects, state, last):
    """Update object/state structures."""
    player_number = obj.OwnerId() if obj.OwnerId() > 0 else None
    if obj.MasterObjectClass() not in [70, 80]:
        return
    if obj.Id() not in objects:
        objects[obj.Id()] = {
            'created': obj.CreatedTime(),
            'destroyed': None,
            'destroyed_by_instance_id': None,
            'deleted': False,
            'pos_x': obj.Position().X(),
            'pos_y': obj.Position().Y()
        }
    elif obj.State() == 4 and obj.Id() in objects:
        data = {
            'destroyed': obj.KilledTime(),
            'deleted': obj.DeletedByOwner()
        }
        if obj.KilledByUnitId() in objects:
            data.update({
                'destroyed_by_instance_id': obj.KilledByUnitId()
            })
        objects[obj.Id()].update(data)


    change = (
        obj.Id() not in last or
        has_diff(last[obj.Id()], player_number=player_number, object_id=obj.MasterObjectId())
    )
    if change:
        state.append({
            'timestamp': tick,
            'instance_id': obj.Id(),
            'player_number': player_number,
            'object_id': obj.MasterObjectId(),
            'class_id': obj.MasterObjectClass(),
        })

    last[obj.Id()] = {
        'player_number': player_number,
        'object_id': obj.MasterObjectId(),
        'class_id': obj.MasterObjectClass()
    }


async def get_extracted_data( # pylint: disable=too-many-arguments, too-many-locals
        header, encoding, diplomacy_type, players, start_time, duration, playback, handle
):
    """Get extracted data."""
    timeseries = []
    research = defaultdict(dict)
    market = []
    objects = {}
    state = []
    last = {}
    chats = get_lobby_chat(header, encoding, diplomacy_type, players)
    client = await Client.create(playback, handle.name, start_time, duration)

    async for tick, source, message in client.sync(timeout=120):
        if source == Source.MGZ and message[0] == fast.Operation.CHAT:
            try:
                chats.append(parse_chat(
                    message[1].decode(encoding), tick, players, diplomacy_type
                ))
            except UnicodeDecodeError:
                LOGGER.warning('could not decode chat')

        elif source == Source.MEMORY:
            update_market(tick, message.MarketCoefficients(), market)

            for i in range(0, message.ObjectsLength()):
                update_objects(tick, message.Objects(i), objects, state, last)

            for i in range(0, message.PlayersLength()):
                player = message.Players(i)
                timeseries.append(build_timeseries_record(tick, player))
                for j in range(0, player.TechsLength()):
                    update_research(player.Id(), player.Techs(j), research)

    handle.close()

    return {
        'chat': chats,
        'timeseries': timeseries,
        'research': flatten_research(research),
        'market': market,
        'objects': [dict(obj, instance_id=i) for i, obj in objects.items()],
        'state': state
    }
