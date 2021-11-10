"""Summary compatibiilty."""
from collections import defaultdict
from mgz.model import parse_match
from mgz.summary.diplomacy import get_diplomacy_type


TC_IDS = [71, 109, 141, 142]
STONE_WALL_ID = 117
PALISADE_WALL_ID = 72


class ModelSummary:
    """Compatibility layer between Model and Summary classes."""

    def __init__(self, handle, playback=None):
        self.match = parse_match(handle)
        self.size = self.match.file.size

    def get_chat(self):
        return [dict(
            player_number=c.player.number,
            message=c.message,
            timestamp=c.timestamp,
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
            starting_resources=None,
            starting_age=None,
            ending_age=None,
            victory_condition=None,
            treaty_length=None,
            multiqueue=self.match.multiqueue
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
            rated=None,
            ratings=None,
            lobby_name=self.match.lobby
        )

    def get_language(self):
        return self.match.file.language

    def get_owner(self):
        return self.match.file.perspective.number

    def get_duration(self):
        return self.match.duration

    def get_completed(self):
        return self.match.completed

    def get_restored(self):
        return False

    def has_achievements(self):
        return False

    def get_version(self):
        return (
            self.match.version.value,
            self.match.game_version,
            self.match.save_version,
            self.match.log_version
        )

    def get_dataset(self):
        return dict(
            id=100,
            name='Definitive Edition',
            version=None
        ), None

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
                rate_snapshot=None,
                cheater=None,
                achievements=None
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
                if obj.class_id not in [10, 30, 70, 80]:
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
            tcs=tcs,
            stone_walls=stone_walls,
            palisade_walls=palisade_walls
        )

    def get_map(self):
        return dict(
            id=self.match.map.id,
            name=self.match.map.name,
            size=self.match.map.size,
            dimension=self.match.map.dimension,
            custom=self.match.map.custom,
            seed=self.match.map.seed,
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


if __name__ == '__main__':
    for f in ['small.mgz', 'tests/recs/de-25.02.aoe2record']:
        print('----------------')
        with open(f, 'rb') as h:
            ms = ModelSummary(h)
        print(ms.get_players())
        print(ms.get_mirror())
        #print(ms.get_platform())
