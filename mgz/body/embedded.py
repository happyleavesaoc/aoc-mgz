"""Embedded Structures.

Various structure can be embedded in the body, without an operation header.

Saved Chapters:

A saved chapter is a header structure embedded in the body.
There is no command identifier, so the command type is actually
the first field of the header - length/offset. Applying the `subheader`
struct at this point will parse the embedded header.


This section is a work in progress.
"""

from construct import (Array, Computed, Embedded, GreedyBytes, If, Int16ul,
                       Int32ul, Padding, Peek, String, Struct, Switch)

from mgz import subheader

# pylint: disable=invalid-name

# Embedded chat message
chat = Struct(
    "subtype"/Computed("chat"),
    "data"/Struct(
        "length"/Computed(lambda ctx: ctx._._._.op),
        "text"/String(lambda ctx: ctx._._._.op, padchar=b'\x00',
                      trimdir='right', encoding='latin1'),
    )
)

# Embedded header (aka saved chapter)
header = Struct(
    "subtype"/Computed("savedchapter"),
    "data"/Struct(
        "header_length"/Computed(lambda ctx: ctx._._._.op - ctx._._._.start),
        Embedded(subheader)
    )
)

# Unknown embedded structure - looks like a partial action?
other = Struct(
    "subtype"/Computed("unknown"),
    "data"/Struct(
        Padding(4),
        "num_ints"/Int32ul,
        If(lambda ctx: ctx.num_ints < 0xff, Array(
            lambda ctx: ctx.num_ints, Int32ul
        )),
        Padding(12)
    )
)

# Anything we don't recognize - just consume the remainder
default = Struct(
    "subtype"/Computed("default"),
    GreedyBytes
)


# Embedded structures identified by first byte (for now)
embedded = "embedded"/Struct(
    "marker"/Peek(Int16ul),
    Embedded("data"/Switch(lambda ctx: ctx.marker, {
        0: header,
        9024: chat,
        65535: other
    }, default=default))
)
