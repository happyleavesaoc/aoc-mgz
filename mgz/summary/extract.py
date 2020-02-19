""""Extract data via playback."""

import logging
from collections import defaultdict

from mgz.playback import Client, Source


LOGGER = logging.getLogger(__name__)
CLASS_UNIT = 70
CLASS_BUILDING = 80
TECH_STATE_AVAILABLE = 2
TECH_STATE_RESEARCHING = 3
TECH_STATE_DONE = 4


def has_diff(data, **kwargs):
    """Simple dict subset diff."""
    for key, value in kwargs.items():
        if data.get(key) != value:
            return True
    return False


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
    if tech.State() == TECH_STATE_RESEARCHING and tech.IdIndex() not in research[player_number]:
        research[player_number][tech.IdIndex()] = {
            'started': tech.LastStateChange(),
            'finished': None
        }
    elif tech.State() == TECH_STATE_DONE and tech.IdIndex() in research[player_number]:
        research[player_number][tech.IdIndex()]['finished'] = tech.LastStateChange()
    elif tech.State() == TECH_STATE_AVAILABLE and tech.IdIndex() in research[player_number]:
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
    if obj.MasterObjectClass() not in [CLASS_UNIT, CLASS_BUILDING]:
        return
    if obj.Id() not in objects:
        objects[obj.Id()] = {
            'created': obj.CreatedTime(),
            'destroyed': None,
            'destroyed_by_instance_id': None,
            'destroyed_building_percent': None,
            'deleted': False,
            'created_x': obj.Position().X(),
            'created_y': obj.Position().Y(),
            'destroyed_x': None,
            'destroyed_y': None,
            'building_started': None,
            'building_completed': None
        }
    elif obj.KilledTime() > 0 and obj.Id() in objects:
        data = {
            'destroyed': obj.KilledTime(),
            'deleted': obj.DeletedByOwner()
        }
        if obj.MasterObjectClass() == CLASS_UNIT:
            data.update({
                'destroyed_x': obj.Position().X(),
                'destroyed_y': obj.Position().Y()
            })
        elif obj.MasterObjectClass() == CLASS_BUILDING:
            data['destroyed_building_percent'] = obj.BuildingPercentComplete()
        if obj.KilledByUnitId() in objects:
            data.update({
                'destroyed_by_instance_id': obj.KilledByUnitId()
            })
        objects[obj.Id()].update(data)
    if obj.MasterObjectClass() == CLASS_BUILDING and obj.Id() in objects:
        if obj.BuildingStartTime() > 0 and objects[obj.Id()]['building_started'] is None:
            objects[obj.Id()]['building_started'] = obj.BuildingStartTime()
        if obj.BuildingCompleteTime() > 0 and objects[obj.Id()]['building_completed'] is None:
            objects[obj.Id()]['building_completed'] = obj.BuildingCompleteTime()

    researching_technology_id = obj.CurrentlyResearchingTechId() if obj.CurrentlyResearchingTechId() > 0 else None
    change = (
        obj.Id() not in last or
        has_diff(
            last[obj.Id()],
            player_number=player_number,
            object_id=obj.MasterObjectId(),
            researching_technology_id=researching_technology_id
        )
    )
    snapshot = {
        'timestamp': tick,
        'instance_id': obj.Id(),
        'player_number': player_number,
        'object_id': obj.MasterObjectId(),
        'class_id': obj.MasterObjectClass(),
        'researching_technology_id': researching_technology_id
    }
    if change:
        state.append(snapshot)
    last[obj.Id()] = snapshot


async def get_extracted_data(start_time, duration, playback, handle, interval):
    """Get extracted data."""
    timeseries = []
    research = defaultdict(dict)
    market = []
    objects = {}
    state = []
    last = {}
    client = await Client.create(playback, handle.name, start_time, duration, interval)
    async for tick, source, message in client.sync():
        if source != Source.MEMORY:
            continue
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
        'timeseries': timeseries,
        'research': flatten_research(research),
        'market': market,
        'objects': [dict(obj, instance_id=i) for i, obj in objects.items()],
        'state': state
    }
