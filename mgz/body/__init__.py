"""Body.

An mgz body is a stream of Operations

An Operation can be:
 - Action: Player input that materially affects the game
 - Chat: Player chat message
 - Synchronization: Time increment
 - Viewlock: View coordinates of recording player
 - Embedded: A variety of embedded structures
"""

from construct import (Struct, Byte, Switch, Embedded, Padding,
                       Int32ul, Peek, Tell, Float32l, String, If, Array, Bytes,
                       GreedyBytes, Computed, IfThenElse, Int16ul, Int64ul, Seek)
from mgz.enums import ActionEnum, OperationEnum
from mgz.body import actions, embedded
from mgz.util import BoolAdapter


# pylint: disable=invalid-name, bad-continuation


# Action.
action_data = "action"/Struct(
    Peek("type_int"/Byte),
    ActionEnum("type"/Byte),
    Embedded("action"/Switch(lambda ctx: ctx.type, {
        "interact": actions.interact,
        "move": actions.move,
        "stop": actions.stop,
        "create": actions.create,
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
        "de_queue": actions.de_queue,
        "postgame": actions.postgame,
        "de_attackmove": actions.de_attackmove,
        "de_autoscout": actions.de_autoscout
    }, default=Struct(
        "unk_action"/Computed(lambda ctx: ctx._.type),
        "bytes"/Bytes(lambda ctx: ctx._._.length - 1)
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
        "unknown"/Bytes(4),
        "sequence"/Int32ul,
        If(lambda ctx: ctx.sequence > 0, Bytes(332)),
        Bytes(8)
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


# Chat.
chat = "chat"/Struct(
    Padding(4),
    "length"/Int32ul,
    "text"/Bytes(lambda ctx: ctx.length - 0),
    Padding(0)
)


# Start.
start = "start"/Struct(
    Seek(-4, whence=1),
    "checksum_interval"/Int32ul,
    BoolAdapter("multiplayer"/Int32ul),
    "rec_owner"/Int32ul,
    BoolAdapter("reveal_map"/Int32ul),
    "use_sequence_numbers"/Int32ul,
    "number_of_chapters"/Int32ul,
    "aok_or_de"/Peek(Int32ul),
    If(lambda ctx: ctx.aok_or_de == 0, Struct(
        Int32ul,
        "aok"/Peek(Int32ul),
        If(lambda ctx: ctx.aok != 2, Int32ul)
    ))
)

# Meta.
meta = "meta"/Struct(
    "next"/Peek(Int32ul),
    "log_version"/If(lambda ctx: ctx.next != 500, Int32ul),
    "checksum_interval"/Int32ul,
    BoolAdapter("multiplayer"/Int32ul),
    "rec_owner"/Int32ul,
    BoolAdapter("reveal_map"/Int32ul),
    "use_sequence_numbers"/Int32ul,
    "number_of_chapters"/Int32ul,
    "aok_or_de"/Peek(Int32ul),
    "m"/If(lambda ctx: ctx.aok_or_de == 0, Struct(
        "v"/Int32ul,
        "aok"/Peek(Int32ul),
        "z"/If(lambda ctx: ctx.aok != 2, Int64ul)
    ))
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
        "chat": chat,
        "embedded": embedded.embedded
    })),
    "end"/Tell
)
