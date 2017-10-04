from construct import *
from mgz.enums import *
from mgz.body.actions import *

"""An mgz body is a stream of Operations

An Operation can be:
 - Action: Player input that materially affects the game
 - Message: Either a start-of-game indicator, or chat
 - Synchronization: Time increment and view coordinates of recording player
 - Saved Chapter: Embedded header structure
"""

"""Action"""
action_data = "action"/Struct(
    ActionEnum("type"/Byte),
    Embedded("action"/Switch(lambda ctx: ctx.type,
        {
            "attack": attack,
            "move": move,
            "stop": stop,
            "stance": stance,
            "guard": guard,
            "follow": follow,
            "formation": formation,
            "multiplayersave": multiplayersave,
            "build": build,
            "gamespeed": gamespeed,
            "patrol": patrol,
            "wall": wall,
            "delete": delete,
            "attackground": attackground,
            "unload": unload,
            "flare": flare,
            "garrison": garrison,
            "gatherpoint": gatherpoint,
            "townbell": townbell,
            "resign": resign,
            "tribute": tribute,
            "train": train,
            "research": research,
            "sell": sell,
            "buy": buy,
            "backtowork": backtowork,
            "postgame": postgame
        },
        default = Padding(lambda ctx: ctx._.length - 1),
    )),
    Padding(4)
)

"""Action - length followed by data"""
action = "action"/Struct(
    "length"/Int32ul,
    action_data
)

"""Synchronization"""
sync = "sync"/Struct(
    "time_increment"/Int32ul,
    "flag"/Int32ul,
    If(lambda ctx: not ctx.flag,
        Padding(28)
    ),
    "view"/Struct(
        "x"/Float32l,
        "y"/Float32l
    ),
    "player_id"/Int32ul
)

"""Chat variation of Message"""
chat = "chat"/Struct(
    "length"/Int32ul,
    "text"/String(lambda ctx: ctx.length, padchar = b'\x00', trimdir = 'right', encoding='latin1')
)

"""Message"""
message = "message"/Struct(
    MessageEnum("subtype"/Int32ul),
    "data"/Switch(lambda ctx: ctx.subtype,
        {
            "start": Padding(20),
            "chat": chat,
        }
    )
)

"""Saved Chapter

A saved chapter is a header structure embedded in the body.
There is no command identifier, so the command type is actually
the first field of the header - length/offset. Therefore, just skip the
number of bytes indicated in `type` minus the current position.

If you wanted to check the game state at this point, you could apply
the header Struct, accounting for having already read the first 4 bytes.
"""
savedchapter = "saved_chapter"/Struct(
    "start"/Tell,
    Padding(lambda ctx: ctx.op - ctx.start),
)

"""Operation"""
operation = "operation"/Struct(
    Peek(OperationEnum("type"/Int32ul)),
    "op"/Int32ul,
    Embedded("data"/Switch(lambda ctx: ctx.type,
        {
            "action": action,
            "sync": sync,
            "message": message,
            "savedchapter": savedchapter
        }
    ))
)
