"""Summary compatibiilty."""
from mgz.model import parse_match


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
            difficulty=None,
            population_limit=self.match.population,
            speed=(
                self.match.speed_id,
                self.match.speed
            ),
            cheats=self.match.cheats,
            team_together=None,
            all_technologies=None,
            lock_speed=None,
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
        return None

    def get_platform(self):
        return dict(
            platform_id=None,
            platform_match_id=None,
            ladder=None,
            rated=None,
            ratings=None,
            lobby_name=None
        )

    def get_language(self):
        return self.match.file.language

    def get_owner(self):
        return self.match.file.perspective.number

    def get_duration(self):
        return self.match.duration

    def get_completed(self):
        return None

    def get_restored(self):
        return False

    def has_achievements(self):
        return None

    def get_version(self):
        return (
            self.match.version.value,
            self.match.game_version,
            self.match.save_version,
            self.match.log_version
        )

    def get_dataset(self):
        return dict(
        )

    def get_teams(self):
        return None

    def get_diplomacy(self):
        return None

    def get_players(self):
        return [
            dict(
                name=p.name,
                number=p.number,
                civilization=p.civilization_id,
                color_id=p.color_id
            ) for p in self.match.players
        ]

    def get_mirror(self):
        return None

    def get_objects(self):
        return None

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
    with open('small.mgz', 'rb') as h:
        ms = ModelSummary(h)
    print(ms.get_players())
    #print(ms.get_settings())
