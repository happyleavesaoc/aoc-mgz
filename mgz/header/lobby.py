"""Lobby."""

from construct import Array, Byte, Bytes, Flag, Int32ul, Padding, Peek, Struct, If

from mgz.enums import GameTypeEnum, RevealMapEnum

# pylint: disable=invalid-name, bad-continuation


# Player inputs in the lobby, and several host settings.
lobby = "lobby"/Struct(
    Array(8, "teams"/Byte), # team number selected by each player
    If(lambda ctx: ctx._.version != 'VER 9.4',
        Padding(1),
    ),
    Peek("reveal_map_id"/Int32ul),
    RevealMapEnum("reveal_map"/Int32ul),
    Padding(4),
    "map_size"/Int32ul,
    "population_limit"/Int32ul, # multiply by 25 for UserPatch 1.4
    Peek("game_type_id"/Byte),
    GameTypeEnum("game_type"/Byte),
    "lock_teams"/Flag,
    If(lambda ctx: ctx._.version == 'VER 9.4',
        Padding(5)
    ),
    "num_chat"/Int32ul,
    Array(
        lambda ctx: ctx.num_chat, # pre-game chat messages
        "messages"/Struct(
            "message_length"/Int32ul,
            "message"/Bytes(lambda ctx: ctx.message_length - (1 if ctx.message_length > 0 else 0)),
            If(lambda ctx: ctx.message_length > 0, Padding(1))
        )
    ),
    If(lambda ctx: ctx._.version == 'VER 9.4',
        Padding(10)
    )
)
