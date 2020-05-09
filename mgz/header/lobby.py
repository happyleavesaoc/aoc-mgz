"""Lobby."""

from construct import Array, Byte, Bytes, Flag, Int32ul, Padding, Peek, Struct, If, Computed, Embedded, Int32sl

from mgz.enums import GameTypeEnum, RevealMapEnum
from mgz.util import Version

# pylint: disable=invalid-name, bad-continuation


# Player inputs in the lobby, and several host settings.
lobby = "lobby"/Struct(
    Array(8, "teams"/Byte), # team number selected by each player
    If(lambda ctx: ctx._.version != Version.DE,
        Padding(1),
    ),
    Peek("reveal_map_id"/Int32ul),
    RevealMapEnum("reveal_map"/Int32ul),
    "fog_of_war"/Int32ul,
    "map_size"/Int32ul,
    "population_limit_encoded"/Int32ul,
    "population_limit"/Computed(lambda ctx: ctx.population_limit_encoded * (25 if ctx._.version in [Version.USERPATCH14, Version.USERPATCH15] else 1)),
    Embedded(If(lambda ctx: ctx._.version != Version.AOK,
        Struct(
            Peek("game_type_id"/Byte),
            GameTypeEnum("game_type"/Byte),
            "lock_teams"/Flag
        )
    )),
    If(lambda ctx: ctx._.version == Version.DE,
        Struct(
            "treaty_length"/Byte,
            "cheat_codes_used"/Int32ul,
            If(lambda ctx: ctx._._.save_version >= 13.13, Padding(4))
        )
    ),
    Embedded(If(lambda ctx: ctx._.version != Version.AOK,
        Struct(
            "num_chat"/Int32ul,
            Array(
                lambda ctx: ctx.num_chat, # pre-game chat messages
                "messages"/Struct(
                    "message_length"/Int32ul,
                    "message"/Bytes(lambda ctx: ctx.message_length - (1 if ctx.message_length > 0 else 0)),
                    If(lambda ctx: ctx.message_length > 0, Padding(1))
                )
            )
        )
    )),
    "de"/If(lambda ctx: ctx._.version == Version.DE,
        Struct(
            "map_seed"/If(lambda ctx: ctx._._.save_version >= 13.08, Int32sl),
            Bytes(10)
        )
    )
)
