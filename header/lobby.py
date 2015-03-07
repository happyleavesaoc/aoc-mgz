from construct import *
from aoc.mgz.enums import *

"""Player inputs in the lobby, and several host settings"""
lobby = Struct("lobby",
	Array(8, Byte("teams")), # team number selected by each player
	Padding(1),
	RevealMapEnum(ULInt32("reveal_map")),
	Padding(8),
	ULInt32("population_limit"), # multiply by 25 for UserPatch 1.4
	GameTypeEnum(Byte("game_type")),
	Flag("lock_teams"),
	ULInt32("num_chat"),
	Array(lambda ctx: ctx.num_chat, # pre-game chat messages
		Struct("messages",
			ULInt32("message_length"),
			String("message", lambda ctx: ctx.message_length, padchar = '\x00', trimdir = 'right')
		)
	)
)