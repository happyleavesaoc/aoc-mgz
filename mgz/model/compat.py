"""Summary compatibility."""
from collections import defaultdict
from mgz.model import parse_match
from mgz.common.diplomacy import get_diplomacy_type
from mgz.common.chat import Chat as ChatType


TC_IDS = [71, 109, 141, 142]
STONE_WALL_ID = 117
PALISADE_WALL_ID = 72


def empty_achievements():
    ach = {}
    ach['military'] = dict(
        score=None,
        units_killed=None,
        units_lost=None,
        buildings_lost=None,
        buildings_razed=None,
        units_converted=None,
        hit_points_killed=None,
        hit_points_razed=None,
    )
    ach['economy'] = dict(
        score=None,
        food_collected=None,
        wood_collected=None,
        stone_collected=None,
        gold_collected=None,
        tribute_sent=None,
        tribute_received=None,
        trade_gold=None,
        relic_gold=None,
    )
    ach['society'] = dict(
        score=None,
        total_relics=None,
        total_castles=None,
        total_wonders=None,
        villager_high=None,
    )
    ach['technology'] = dict(
        score=None,
        explored_percent=None,
        research_count=None,
        research_percent=None,
        feudal_time=None,
        castle_time=None,
        imperial_time=None,
    )
    return ach


class ModelSummary:
    """Compatibility layer between Model and Summary classes."""

    def __init__(self, handle):
        self.match = parse_match(handle)
        self.size = self.match.file.size

    def get_chat(self):
        return [dict(
            type=ChatType.MESSAGE,
            player_number=c.player.number,
            message=c.message,
            timestamp=c.timestamp.total_seconds() * 1000,
            origination=c.origination,
            audience=c.audience
        ) for c in self.match.chat]

    def get_settings(self):
        return dict(
            type=(
                self.match.type_id,
                self.match.type
            ),
            difficulty=(
                self.match.difficulty_id,
                self.match.difficulty
            ),
            population_limit=self.match.population,
            speed=(
                self.match.speed_id,
                self.match.speed
            ),
            cheats=self.match.cheats,
            team_together=self.match.team_together,
            all_technologies=self.match.all_technologies,
            lock_speed=self.match.lock_speed,
            lock_teams=self.match.lock_teams,
            map_reveal_choice=(
                self.match.map_reveal_id,
                self.match.map_reveal
            ),
            diplomacy_type=self.match.diplomacy_type,
            starting_resources=(0, 'Standard'),
            starting_age=(
                self.match.starting_age_id,
                self.match.starting_age
            ),
            ending_age=(3, 'Imperial'),
            victory_condition=(1, 'Conquest'),
            treaty_length=None,
            multiqueue=self.match.multiqueue,
            hidden_civs=self.match.hidden_civs
        )

    def get_file_hash(self):
        return self.match.file.hash

    def get_encoding(self):
        return self.match.file.encoding.name

    def get_hash(self):
        return self.match.hash

    def get_platform(self):
        return dict(
            platform_id='de',
            platform_match_id=self.match.guid,
            ladder=None,
            rated=self.match.rated,
            ratings=None,
            lobby_name=self.match.lobby,
            spec_delay=int(self.match.spec_delay.total_seconds()),
            allow_specs=self.match.allow_specs,
            private=self.match.private
        )

    def get_language(self):
        return self.match.file.language

    def get_device(self):
        return self.match.file.device_type

    def get_owner(self):
        return self.match.file.perspective.number

    def get_duration(self):
        return self.match.duration.total_seconds() * 1000

    def get_completed(self):
        return self.match.completed

    def get_restored(self):
        return self.match.restored, self.match.restored_at.total_seconds() * 1000

    def has_achievements(self):
        return False

    def get_version(self):
        return (
            self.match.version,
            self.match.game_version,
            self.match.save_version,
            self.match.log_version,
            self.match.build_version
        )

    def get_played(self):
        return self.match.timestamp.timestamp() if self.match.timestamp else None

    def get_postgame(self):
        return None

    def get_dataset(self):
        if self.match.dataset_id == 101:
            return dict(
                id=101,
                name='Return of Rome',
                version=None
            )
        return dict(
            id=100,
            name='Definitive Edition',
            version=None
        )

    def get_teams(self):
        return [[p.number for p in t] for t in self.match.teams]

    def get_diplomacy(self):
        d_type = get_diplomacy_type(self.match.teams, self.match.players)
        team_sizes = sorted([len(team) for team in self.match.teams])
        ts = 'v'.join([str(size) for size in team_sizes])
        if d_type == 'FFA':
            ts = 'FFA'
        return dict(
            type=d_type,
            team_size=ts
        )

    def get_players(self):
        return [
            dict(
                name=p.name,
                number=p.number,
                civilization=p.civilization_id,
                color_id=p.color_id,
                human=True,
                winner=p.winner,
                user_id=p.profile_id,
                position=(p.position.x, p.position.y),
                mvp=None,
                score=None,
                rate_snapshot=p.rate_snapshot,
                cheater=None,
                achievements=empty_achievements(),
                prefer_random=p.prefer_random,
                eapm=p.eapm
            ) for p in self.match.players
        ]

    def get_mirror(self):
        mirror = False
        if self.get_diplomacy()['type'] == '1v1':
            civs = set()
            for data in self.get_players():
                civs.add(data['civilization'])
            mirror = (len(civs) == 1)
        return mirror

    def get_objects(self):
        output = []
        tcs = defaultdict(int)
        stone_walls = {}
        palisade_walls = {}
        objects = [(None, self.match.gaia)]
        for player in self.match.players:
            objects.append((player.number, player.objects))
        for player_number, objs in objects:
            for obj in objs:
                if obj.class_id not in [10, 20, 30, 70, 80]:
                    continue
                if obj.index == 1:
                    continue
                if obj.object_id in TC_IDS:
                    tcs[player_number] += 1
                if obj.object_id == STONE_WALL_ID:
                    stone_walls[player_number] = True
                if obj.object_id == PALISADE_WALL_ID:
                    palisade_walls[player_number] = True
                output.append(dict(
                    object_id=obj.object_id,
                    instance_id=obj.instance_id,
                    class_id=obj.class_id,
                    player_number=player_number,
                    x=obj.position.x,
                    y=obj.position.y
                ))
        return dict(
            objects=output,
            tcs=max(tcs.values()) if len(tcs.values()) > 0 else None,
            stone_walls=bool(stone_walls) and all(stone_walls.values()),
            palisade_walls=bool(palisade_walls) and all(palisade_walls.values())
        )

    def get_map(self):
        return dict(
            id=self.match.map.id if not self.match.map.custom else None,
            name=self.match.map.name,
            size=self.match.map.size,
            dimension=self.match.map.dimension,
            custom=self.match.map.custom,
            seed=self.match.map.seed,
            mod_id=self.match.map.mod_id,
            modes=self.match.map.modes,
            zr=self.match.map.zr,
            water=None,
            tiles=[
                dict(
                    x=t.position.x,
                    y=t.position.y,
                    elevation=t.elevation,
                    terrain_id=t.terrain
                ) for t in self.match.map.tiles
            ]
        )
