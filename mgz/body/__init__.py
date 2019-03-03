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
from mgz.util import BoolAdapter


# pylint: disable=invalid-name


# Action.
action_data = "action"/Struct(
    Peek("type_int"/Byte),
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
        "give_attribute": actions.give_attribute,
        "add_attribute": actions.add_attribute,
        "ai_waypoint": actions.ai_waypoint,
        "ai_interact": actions.ai_interact,
        "ai_move": actions.ai_move,
        "ai_queue": actions.ai_queue,
        "save": actions.save,
        "chapter": actions.chapter,
        "ai_command": actions.ai_command,
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
    Peek("next"/Int32ul),
    "checksum"/If(lambda ctx: not ctx.next, Struct(
        Padding(8),
        "sync"/Int32ul,
        Padding(16)
    ))
)


# View lock.
viewlock = "viewlock"/Struct(
    "view"/Struct(
        "x"/Float32l,
        "y"/Float32l
    ),
    "player_id"/Int32ul
)


# Chat variation of Message.
chat = "chat"/Struct(
    Padding(4),
    "length"/Int32ul,
    "text"/Bytes(lambda ctx: ctx.length - 1),
    Padding(1)
)

# Game start
start = "start"/Struct(
    "checksum_interval"/Int32ul,
    BoolAdapter("multiplayer"/Int32ul),
    "rec_owner"/Int32ul,
    BoolAdapter("reveal_map"/Int32ul),
    "record_sequence_numbers"/Int32ul,
    "number_of_chapters"/Int32ul
)


# Message.
message = "message"/Struct(
    MessageEnum("subtype"/Peek(Int32ul)),
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
        "viewlock": viewlock,
        "message": message,
        "embedded": embedded.embedded
    })),
    "end"/Tell
)
