from construct import *
from aoc.mgz.enums import *
from aoc.mgz.body.actions import *

"""An mgz body is a stream of Operations

An Operation can be:
 - Action: Player input that materially affects the game
 - Message: Either a start-of-game indicator, or chat
 - Synchronization: Time increment and view coordinates of recording player
 - Saved Chapter: Embedded header structure
"""

"""Action"""
action_data = Struct("action",
	ActionEnum(Byte("type")),
	Embed(Switch("action", lambda ctx: ctx.type,
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
action = Struct("action",
	ULInt32("length"),
	action_data
)

"""Synchronization"""
sync = Struct("sync",
	ULInt32("time_increment"),
	ULInt32("flag"),
	If(lambda ctx: not ctx.flag,
		Padding(28)
	),
	Struct("view",
		LFloat32("x"),
		LFloat32("y")
	),
	ULInt32("player_id")
)

"""Chat variation of Message"""
chat = Struct("chat",
	ULInt32("length"),
	String("text", lambda ctx: ctx.length, padchar = '\x00', trimdir = 'right')
)

"""Message"""
message = Struct("message",
	MessageEnum(ULInt32("subtype")),
	Switch("data", lambda ctx: ctx.subtype,
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
savedchapter = Struct("saved_chapter",
	Anchor("start"),
	Padding(lambda ctx: ctx.op - ctx.start),
)

"""Operation"""
operation = Struct("operation",
	Peek(OperationEnum(ULInt32("type"))),
	ULInt32("op"),
	Embed(Switch("data", lambda ctx: ctx.type,
		{
			"action": action,
			"sync": sync,
			"message": message,
			"savedchapter": savedchapter
		}
	))
)