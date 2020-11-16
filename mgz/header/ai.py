"""AI."""

from mgz import Version
from mgz.util import Find
from construct import (Array, Byte, If, Int16ul, Int32sl, Int32ul, Padding,
                       PascalString, Struct, this, IfThenElse)

# pylint: disable=invalid-name

script = "script"/Struct(
    Padding(4),
    "seq"/Int32sl,
    "max_rules"/Int16ul,
    "num_rules"/Int16ul,
    Padding(4),
    Array(this.num_rules, "rules"/Struct(
        Padding(12),
        "num_facts"/Byte,
        "num_facts_actions"/Byte,
        Padding(2),
        Array(16, "data"/Struct(
            "type"/Int32ul,
            "id"/Int16ul,
            Padding(2),
            Array(4, "params"/Int32ul)
        ))
    ))
)

ai = "ai"/Struct(
    "has_ai"/Int32ul, # if true, parse AI
    "yep"/If(
        this.has_ai == 1,
        IfThenElse(
            lambda ctx: ctx._.version == Version.DE,
            Find(b'\00' * 4096, None),  # The ai structure in DE seems to have changed, for now we simply skip it
            "ais"/Struct(
                "max_strings"/Int16ul,
                "num_strings"/Int16ul,
                Padding(4),
                Array(this.num_strings, "strings"/PascalString(lengthfield="name_length"/Int32ul,
                                                               encoding='latin1')),
                Padding(6),
                Array(8, script),
                Padding(104),
                Array(80, "timers"/Int32sl),
                Array(256, "shared_goals"/Int32sl),
                Padding(4096),
            )
        )
    )
)
