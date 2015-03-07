from construct import *
from actions import *



body = OptionalGreedyRange(
	Struct("body",
		OperationEnum(ULInt32("operation")),
		Embed(Switch("data", lambda ctx: ctx.operation,
			{
				"action": action,
				"sync": sync,
				"message": message,
			}
		))
	)
)