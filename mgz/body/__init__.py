"""Body.

An mgz body is a stream of Operations

An Operation can be:
 - Action: Player input that materially affects the game
 - Message: Either a start-of-game indicator, or chat
 - Synchronization: Time increment and view coordinates of recording player
 - Embedded: A variety of embedded structures
"""

from construct import (Struct, Byte, Switch, Embedded, Padding,
                       Int32ul, Peek, Tell, Float32l, String, If, Array, Bytes,
                       GreedyBytes, Computed, IfThenElse, Int16ul, Probe)
from mgz.enums import ActionEnum, OperationEnum, MessageEnum
from mgz.body import actions, embedded


# pylint: disable=invalid-name


# Action.
action_data = "action"/Struct(
    ActionEnum("type"/Byte),
    Embedded("action"/Switch(lambda ctx: ctx.type, {
        "interact": actions.interact,
        "move": actions.move,
        "stop": actions.stop,
        "stance": actions.stance,
        "guard": actions.guard,
        "follow": actions.follow,
        "formation": actions.formation,
        "waypoint": actions.waypoint,
        "ai_waypoint": actions.ai_waypoint,
        "ai_interact": actions.ai_interact,
        "ai_move": actions.ai_move,
        "ai_queue": actions.ai_queue,
        "save": actions.save,
        "chapter": actions.chapter,
        "unknown": actions.unknown,
        "spec": actions.spec,
        "build": actions.build,
        "game": actions.game,
        "patrol": actions.patrol,
        "wall": actions.wall,
        "delete": actions.delete,
        "attackground": actions.attackground,
        "repair": actions.repair,
        "release": actions.release,
        "togglegate": actions.togglegate,
        "flare": actions.flare,
        "order": actions.order,
        "droprelic": actions.droprelic,
        "gatherpoint": actions.gatherpoint,
        "townbell": actions.townbell,
        "resign": actions.resign,
        "tribute": actions.tribute,
        "queue": actions.queue,
        "multiqueue": actions.multiqueue,
        "research": actions.research,
        "sell": actions.sell,
        "buy": actions.buy,
        "backtowork": actions.backtowork,
        "postgame": actions.postgame
    }, default=Struct(
        "unk_action"/Computed(lambda ctx: ctx._.type),
        "bytes"/Bytes(lambda ctx: ctx._._.length - 1),
        Probe()
    ))),
    Padding(4)
)


# Action - length followed by data.
action = "action"/Struct(
    "length"/Int32ul,
    action_data
)


# Synchronization.
sync = "sync"/Struct(
    "time_increment"/Int32ul,
    "flag"/Int32ul,
    If(lambda ctx: not ctx.flag, Padding(
        28
    )),
    "view"/Struct(
        "x"/Float32l,
        "y"/Float32l
    ),
    "player_id"/Int32ul
)


# Chat variation of Message.
chat = "chat"/Struct(
    "length"/Int32ul,
    "text"/String(lambda ctx: ctx.length, padchar=b'\x00', trimdir='right', encoding='latin1')
)

# Game start
start = "start"/Struct(
    "unk1"/Int32ul,
    "rec_owner"/Int32ul,
    "unk2"/Int32ul,
    "unk3"/Int32ul,
    "unk4"/Int32ul
)


# Message.
message = "message"/Struct(
    MessageEnum("subtype"/Int32ul),
    "data"/Switch(lambda ctx: ctx.subtype, {
        "start": start,
        "chat": chat
    })
)


# Operation.
operation = "operation"/Struct(
    Peek(OperationEnum("type"/Int32ul)),
    "start"/Tell,
    "op"/Int32ul,
    Embedded("data"/Switch(lambda ctx: ctx.type, {
        "action": action,
        "sync": sync,
        "message": message,
        "embedded": embedded.embedded
    })),
    "end"/Tell
)
