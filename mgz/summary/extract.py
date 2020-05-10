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
DE_TECH_STATE_AVAILABLE = 1
DE_TECH_STATE_RESEARCHING = 2
DE_TECH_STATE_DONE = 3
DE_TECH_STATE_CANT_RESEARCH = -1
STATUS_WINNER = 1


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


def build_fb_timeseries_record(tick, player):
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


def build_json_timeseries_record(tick, player):
    """Build a timeseries record."""
    return {
        'timestamp': tick,
        'player_number': player['id'],
        'population': player['attributes']['population'],
        'military': player['attributes']['militaryPopulation'],
        'percent_explored': player['attributes']['percentMapExplored'],
        'headroom': int(player['attributes']['populationFreeRoom']),
        'food': int(player['attributes']['food']),
        'wood': int(player['attributes']['wood']),
        'stone': int(player['attributes']['stone']),
        'gold': int(player['attributes']['gold']),
        'total_housed_time': int(player['cumulativeHousedTime']),
        'total_popcapped_time': int(player['cumulativePopCappedTime']),
        'relics_captured': int(player['attributes']['relicsCaptured']),
        'relic_gold': int(player['attributes']['relicIncomeSum']),
        'trade_profit': int(player['attributes']['tradeIncomeSum']),
        'tribute_received': int(player['attributes']['tributeReceived']),
        'tribute_sent': int(player['attributes']['tributeSent']),
        'total_food': int(player['attributes']['foodTotalGathered']),
        'total_wood': int(player['attributes']['woodTotalGathered']),
        'total_gold': int(player['attributes']['goldTotalGathered']),
        'total_stone': int(player['attributes']['stoneTotalGathered']),
        'value_spent_objects': int(player['attributes']['objectCostSum']),
        'value_spent_research': int(player['attributes']['techCostSum']),
        'value_lost_units': int(player['attributes']['unitsLostValue']),
        'value_lost_buildings': int(player['attributes']['buildingsLostValue']),
        'value_current_units': int(player['attributes']['valueOfArmy']),
        'value_current_buildings': int(player['attributes']['valueOfBuildings']),
        'value_objects_destroyed': int(player['attributes']['killsValue'] + player['attributes']['razingsValue']),
        'value_units_killed': int(player['attributes']['killsValue']),
        'value_buildings_razed': int(player['attributes']['razingsValue']),
        'trained': int(player['attributes']['totalUnitsTrained']),
        'converted': int(player['attributes']['unitsConverted']),
        'kills': int(player['attributes']['unitsKilled']),
        'deaths': int(player['attributes']['unitsLost']),
        'razes': int(player['attributes']['razings']),
        'buildings_lost': int(player['attributes']['buildingsLost']),
        'hit_points_razed': int(player['attributes']['hitPointsRazed']),
        'hit_points_killed': int(player['attributes']['hitPointsKilled']),
        'villager_high': int(player['victoryPoints']['maxVillagers']),
        'military_high': int(player['victoryPoints']['maxMilitary']),
        'total_score': int(player['victoryPoints']['total']),
        'military_score': int(player['victoryPoints']['military']),
        'economy_score': int(player['victoryPoints']['economy']),
        'society_score': int(player['victoryPoints']['society']),
        'technology_score': int(player['victoryPoints']['technology'])
    }


def update_research(player_number, state, index, tick, research, researching_state, done_state, available_state):
    """Update research structure."""
    if state == researching_state and index not in research[player_number]:
        research[player_number][index] = {
            'started': tick,
            'finished': None
        }
    elif state == done_state and index in research[player_number]:
        research[player_number][index]['finished'] = tick
    elif state == available_state and index in research[player_number]:
        del research[player_number][index]


def update_market(tick, food, wood, stone, market):
    """Update market coefficients structure."""
    last = None
    change = True
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


def add_objects(owner_id, instance_id, class_id, object_id, created, pos_x, pos_y, objects):
    """Add objects."""
    player_number = owner_id if owner_id > 0 else None
    if class_id not in [CLASS_UNIT, CLASS_BUILDING]:
        return
    if instance_id not in objects:
        objects[instance_id] = {
            'initial_player_number': player_number,
            'initial_object_id': object_id,
            'initial_class_id': class_id,
            'created': created,
            'destroyed': None,
            'destroyed_by_instance_id': None,
            'destroyed_building_percent': None,
            'deleted': False,
            'created_x': pos_x,
            'created_y': pos_y,
            'destroyed_x': None,
            'destroyed_y': None,
            'building_started': None,
            'building_completed': None,
            'total_idle_time': None
        }


def update_objects(tick, owner_id, instance_id, class_id, object_id, killed, deleted, pos_x, pos_y, percent, killed_by, start, complete, idle, tech_id, objects, state, last):
    """Update object/state structures."""
    player_number = owner_id if owner_id and owner_id > 0 else None
    if instance_id not in objects:
        return
    if not class_id:
        class_id = objects[instance_id]['initial_class_id']
    if not killed:
        killed = objects[instance_id].get('killed')
    data = {}
    if class_id == CLASS_UNIT and pos_x is not None and pos_y is not None:
        data.update({
            'destroyed_x': pos_x,
            'destroyed_y': pos_y
        })

    if killed and killed > 0 and instance_id in objects:
        data.update({
            'destroyed': killed,
            'deleted': deleted
        })
        if class_id == CLASS_BUILDING:
            data['destroyed_building_percent'] = percent
        if killed in objects:
            data.update({
                'destroyed_by_instance_id': killed_by
            })
    objects[instance_id].update(data)

    if class_id == CLASS_BUILDING and instance_id in objects:
        if start and start > 0 and objects[instance_id]['building_started'] is None:
            objects[instance_id]['building_started'] = start
        if complete and complete > 0 and objects[instance_id]['building_completed'] is None:
            objects[instance_id]['building_completed'] = complete

    if instance_id in objects and idle:
        objects[instance_id]['total_idle_time'] = int(idle)

    researching_technology_id = tech_id if tech_id and tech_id > 0 else None
    change = (
        instance_id not in last or
        has_diff(
            last[instance_id],
            player_number=player_number,
            object_id=class_id,
            researching_technology_id=researching_technology_id
        )
    )
    snapshot = {
        'timestamp': tick,
        'instance_id': instance_id,
        'player_number': player_number,
        'object_id': object_id,
        'class_id': class_id,
        'researching_technology_id': researching_technology_id
    }
    if change:
        state.append(snapshot)
    last[instance_id] = snapshot


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
    version = None
    start = time.time()
    client = await Client.create(playback, handle.name, start_time, duration, interval)
    async for tick, source, message in client.sync():
        if source == Source.MEMORY:
            if not version:
                version = message.StateReaderVersion().decode('ascii')

            update_market(tick, message.MarketCoefficients().Food(), message.MarketCoefficients().Wood(), message.MarketCoefficients().Stone(), market)

            # Add any new objects before updating to ensure fks are present for updates
            for i in range(0, message.ObjectsLength()):
                obj = message.Objects(i)
                add_objects(obj.OwnerId(), obj.Id(), obj.MasterObjectClass(), obj.MasterObjectId(), obj.CreatedTime(), obj.Position().X(), obj.Position().Y(), objects)

            for i in range(0, message.ObjectsLength()):
                obj = message.Objects(i)
                update_objects(
                    tick, obj.OwnerId(), obj.Id(), obj.MasterObjectClass(), obj.MasterObjectId(), obj.KilledTime(),
                    obj.DeletedByOwner(), obj.Position().X(), obj.Position().Y(), obj.BuildingPercentComplete(),
                    obj.KilledByUnitId(), obj.BuildingStartTime(), obj.BuildingCompleteTime(), obj.CumulativeIdleTime(),
                    obj.CurrentlyResearchingTechId(), objects, state, last
                )

            for i in range(0, message.PlayersLength()):
                player = message.Players(i)
                timeseries.append(build_fb_timeseries_record(tick, player))
                for j in range(0, player.TechsLength()):
                    tech = player.Techs(j)
                    update_research(
                        player.Id(), tech.State(), tech.IdIndex(), tech.Time(), research,
                        TECH_STATE_RESEARCHING, TECH_STATE_DONE, TECH_STATE_AVAILABLE
                    )

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
        'actions': list(enrich_actions(actions, objects, state)),
        'winners': set()
    }


def external_extracted_data(data, seed_objects, actions):
    """Merge externally-sourced extracted data."""
    research = defaultdict(dict)
    objects = transform_seed_objects(seed_objects)
    state = []
    market = []
    last = {}
    timeseries = []
    winners = set()
    version = data['version']
    interval = data['messageInterval']
    for message in data['messages']:
        update_market(message['time'], message['world']['foodPrice'], message['world']['woodPrice'], message['world']['stonePrice'], market)

        # Add any new objects before updating to ensure fks are present for updates
        for obj in message['objects']:
            # Only add objects the first time we see them
            if 'ownerId' not in obj or 'masterObjectClass' not in obj:
                continue
            add_objects(
                obj['ownerId'], obj['id'], obj['masterObjectClass'], obj['masterObjectId'], obj['createdTime'],
                obj['position']['x'], obj['position']['y'], objects
            )

        for obj in message['objects']:
            update_objects(
                message['time'], obj.get('ownerId'), obj['id'], obj.get('masterObjectClass'), obj.get('masterObjectId'),
                obj.get('killedTime'), None, obj.get('position', {}).get('x'), obj.get('position', {}).get('y'), obj.get('buildingPercentComplete'),
                None, obj.get('buildingStartTime'), obj.get('buildingCompleteTime'), obj.get('cumulativeIdleTime'), None, objects, state, last
            )

        for player in message['players'][1:]:
            timeseries.append(build_json_timeseries_record(message['time'], player))
            if player['status'] == STATUS_WINNER:
                winners.add(player['id'])

        for event in message['events']:
            if event['data']['tag'] == 'techStateChange':
                update_research(
                    event['data']['playerId'], event['data']['state'], event['data']['index'], event['worldTime'],
                    research, DE_TECH_STATE_RESEARCHING, DE_TECH_STATE_DONE, DE_TECH_STATE_AVAILABLE
                )

    for obj in objects.values():
        if not obj['destroyed']:
            obj['destroyed_x'] = None
            obj['destroyed_y'] = None

    return {
        'version': version,
        'interval': interval,
        'runtime': None,
        'timeseries': timeseries,
        'research': flatten_research(research),
        'market': market,
        'objects': [dict(obj, instance_id=i) for i, obj in objects.items()],
        'state': state,
        'actions': list(enrich_actions(actions, objects, state)),
        'winners': winners,
        'available_techs': available_techs
    }
