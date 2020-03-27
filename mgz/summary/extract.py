""""Extract data via playback."""

import logging
import time
from collections import defaultdict
from datetime import timedelta

from mgz import fast
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
        'total_housed_time': int(player.CumulativeHousedTime()),
        'total_popcapped_time': int(player.CumulativePopCappedTime()),
        'relics_captured': int(player.VictoryPointsAndAttributes().VpRelicsCaptured()),
        'relic_gold': int(player.VictoryPointsAndAttributes().VpRelicGold()),
        'trade_profit': int(player.VictoryPointsAndAttributes().VpTradeProfit()),
        'tribute_received': int(player.VictoryPointsAndAttributes().VpTributeReceived()),
        'tribute_sent': int(player.VictoryPointsAndAttributes().VpTributeSent()),
        'total_food': int(player.VictoryPointsAndAttributes().VpTotalFood()),
        'total_wood': int(player.VictoryPointsAndAttributes().VpTotalWood()),
        'total_gold': int(player.VictoryPointsAndAttributes().VpTotalGold()),
        'total_stone': int(player.VictoryPointsAndAttributes().VpTotalStone()),
        'value_spent_objects': int(player.VictoryPointsAndAttributes().AttrValueSpentObjects()),
        'value_spent_research': int(player.VictoryPointsAndAttributes().AttrValueSpentResearch()),
        'value_lost_units': int(player.VictoryPointsAndAttributes().AttrValueLostUnits()),
        'value_lost_buildings': int(player.VictoryPointsAndAttributes().AttrValueLostBuildings()),
        'value_current_units': int(player.VictoryPointsAndAttributes().AttrValueCurrentUnits()),
        'value_current_buildings': int(player.VictoryPointsAndAttributes().AttrValueCurrentBuildings()),
        'value_objects_destroyed': int(player.VictoryPointsAndAttributes().AttrValueObjectsDestroyed()),
        'kills': int(player.VictoryPointsAndAttributes().AttrKills()),
        'deaths': int(player.VictoryPointsAndAttributes().AttrDeaths()),
        'razes': int(player.VictoryPointsAndAttributes().AttrRazes())
    }


def update_research(player_number, tech, research):
    """Update research structure."""
    if tech.State() == TECH_STATE_RESEARCHING and tech.IdIndex() not in research[player_number]:
        research[player_number][tech.IdIndex()] = {
            'started': tech.Time(),
            'finished': None
        }
    elif tech.State() == TECH_STATE_DONE and tech.IdIndex() in research[player_number]:
        research[player_number][tech.IdIndex()]['finished'] = tech.Time()
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


def add_objects(obj, objects):
    """Add objects."""
    player_number = obj.OwnerId() if obj.OwnerId() > 0 else None
    if obj.MasterObjectClass() not in [CLASS_UNIT, CLASS_BUILDING]:
        return
    if obj.Id() not in objects:
        objects[obj.Id()] = {
            'initial_player_number': player_number,
            'initial_object_id': obj.MasterObjectId(),
            'initial_class_id': obj.MasterObjectClass(),
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
            'building_completed': None,
            'total_idle_time': None
        }


def update_objects(tick, obj, objects, state, last):
    """Update object/state structures."""
    player_number = obj.OwnerId() if obj.OwnerId() > 0 else None
    if obj.MasterObjectClass() not in [CLASS_UNIT, CLASS_BUILDING]:
        return
    if obj.KilledTime() > 0 and obj.Id() in objects:
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

    if obj.Id() in objects:
        objects[obj.Id()]['total_idle_time'] = int(obj.CumulativeIdleTime())

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


def enrich_actions(actions, objects, states):
    """Attach player to anonymous actions."""
    owners = defaultdict(list)
    for state in states:
        owners[state['instance_id']].append((state['timestamp'], state['player_number']))
    last_tick = None
    last_seen = []
    for (tick, action_type, payload) in actions:
        if 'player_id' not in payload and 'object_ids' in payload:
            for object_id in payload['object_ids']:
                if object_id not in owners:
                    continue
                for (timestamp, player_number) in owners[object_id]:
                    if timestamp > tick:
                        payload['player_id'] = player_number
                        break
                if object_id not in objects:
                    continue
                if 'player_id' not in payload:
                    payload['player_id'] = objects[object_id]['initial_player_number']
                    break
        action = (tick, action_type, payload)
        if tick != last_tick:
            last_seen = []
            last_tick = tick
        if action not in last_seen and 'player_id' in payload and payload['player_id'] is not None:
            yield action
            last_seen.append(action)


def transform_seed_objects(objects):
    """Map seed objects to state format."""
    return {obj['instance_id']: {
        'initial_player_number': obj['player_number'],
        'initial_object_id': obj['object_id'],
        'initial_class_id': obj['class_id'],
        'created': 0,
        'created_x': obj['x'],
        'created_y':obj['y'],
        'destroyed': None,
        'destroyed_by_instance_id': None,
        'destroyed_building_percent': None,
        'deleted': False,
        'destroyed_x': None,
        'destroyed_y': None,
        'building_started': None,
        'building_completed': None,
        'total_idle_time': None
    } for obj in objects}


async def get_extracted_data(start_time, duration, playback, handle, interval, seed_objects):
    """Get extracted data."""
    timeseries = []
    research = defaultdict(dict)
    market = []
    objects = transform_seed_objects(seed_objects)
    state = []
    last = {}
    actions = []
    tribute = []
    transactions = []
    formations = []
    version = None
    start = time.time()
    client = await Client.create(playback, handle.name, start_time, duration, interval)
    async for tick, source, message in client.sync():
        if source == Source.MEMORY:
            if not version:
                version = message.StateReaderVersion().decode('ascii')

            update_market(tick, message.MarketCoefficients(), market)

            # Add any new objects before updating to ensure fks are present for updates
            for i in range(0, message.ObjectsLength()):
                add_objects(message.Objects(i), objects)

            for i in range(0, message.ObjectsLength()):
                update_objects(tick, message.Objects(i), objects, state, last)

            for i in range(0, message.PlayersLength()):
                player = message.Players(i)
                timeseries.append(build_timeseries_record(tick, player))
                for j in range(0, player.TechsLength()):
                    update_research(player.Id(), player.Techs(j), research)

        elif source == Source.MGZ:
            if message[0] == fast.Operation.ACTION:
                actions.append((tick, *message[1]))

    handle.close()

    return {
        'version': version,
        'runtime': timedelta(seconds=int(time.time() - start)),
        'timeseries': timeseries,
        'research': flatten_research(research),
        'market': market,
        'objects': [dict(obj, instance_id=i) for i, obj in objects.items()],
        'state': state,
        'actions': list(enrich_actions(actions, objects, state))
    }
