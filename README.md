# mgz

Age of Empires II recorded game parsing and summarization in Python 3.

## Supported Versions

- Age of Kings (`.mgl`)
- The Conquerors (`.mgx`)
- Userpatch 1.4 (`.mgz`)
- Userpatch 1.5 (`.mgz`)
- HD Edition >= 4.6 (`.aoe2record`)
- Definitive Edition (`.aoe2record`)

## Architecture

The core functionality of `mgz` is a parser that produces a Python data structure based on a recorded game file. It also offers abstracted representations that make it easier to use the data.

### Parsers

`mgz` offers two parsers, `fast` and `full`. The `fast` parser skips data that is rarely needed, while the `full` parser tries to parse as much as possible. Naturally, the `fast` parser is faster than the `full` parser.
The `full` parser can do just about everything, the `fast` only maybe 80-90%. The `summary` will automatically try the `fast` parser and fall back to the `full` parser if needed.

### Abstractions

Abstractions take parser output as input and return an object with normalized data that is easier to use for most cases. There are two abstractions available, `summary` and `model`. The `summary` abstraction attempts to expose the maximum amount of usable data. The `model` abstraction is more limited but automatically performs more lookups.

## Support

| Version | model | summary | fast (header) | fast (body) | full (header) | full (body) | 
| --- | :-: | :-: | :-: | :-: | :-: | :-: |
| Age of Kings (`.mgl`) | | ✓ | | ✓ | ✓ | |
| The Conquerors (`.mgx`) | | ✓ | | ✓ | ✓ | |
| Userpatch <= 1.4 (`.mgz`) | | ✓ | | ✓ | ✓ | ✓ |
| Userpatch 1.5 (`.mgz`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HD Edition >= 4.6 | | ✓ | | ✓ | ✓ | ✓ |
| HD Edition 5.8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Definitive Edition <= 13.34 (`.aoe2record`) | | ✓ | | ✓ | ✓ | ✓ |
| Definitive Edition > 13.34, <= 26.21 (`.aoe2record`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Definitive Edition > 26.21 (`.aoe2record`) | ✓ | ✓ | ✓ | ✓ | ✓ | |

## Examples

#### Full Parser (header) + Fast Parser (body)

```python
import os
from mgz import header, fast

with open('/path/to/file', 'rb') as data:
    eof = os.fstat(data.fileno()).st_size
    header.parse_stream(data)
    fast.meta(data)
    while data.tell() < eof:
        fast.operation(data)
```

### Summary

```python
from mgz.summary import Summary

with open('/path/to/file', 'rb') as data:
    s = Summary(data)
    s.get_map()
    s.get_platform()
    # ... etc
```

### Model

```python
from mgz.model import parse_match

with open('/path/to/file', 'rb') as data:
    match = parse_match(data)
    match.map.name
    match.file.perspective.number
    # ... etc
```

## To JSON

```python
import json
from mgz.model import parse_match, serialize

with open('/path/to/file', 'rb') as h:
    match = parse_match(h)
    print(json.dumps(serialize(match), indent=2))
```

## Frequently Asked Questions

**Q:** Where are the end-of-game achievements/statistics?

**A:** In the `postgame` action, available only from Userpatch version.

**Q:** How can I tell the number of resources/kills/etc at a certain point?

**A:** You can't, without replaying the match in-game.

**Q:** How does a recorded game file work?

**A:** The first portion (the `header`) is a snapshot of the initial game state. The second portion (the `body`) is a list of moves made by players. The game loads the header, then applies each move to mutate the state according to the game rules.

**Q:** How can I install this package?

**A:** `pip install mgz`

## Contribution
 - Pull requests & patches welcome

## Resources
 - aoc-mgx-format: https://github.com/stefan-kolb/aoc-mgx-format
 - recage: https://github.com/goto-bus-stop/recage
 - recanalyst: http://sourceforge.net/p/recanalyst/
 - genie-rs: https://github.com/SiegeEngineers/genie-rs/tree/default/crates/genie-rec
 - bari-mgx-format: https://web.archive.org/web/20090215065209/http://members.at.infoseek.co.jp/aocai/mgx_format.html
