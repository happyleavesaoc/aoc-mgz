# mgz

Age of Empires II recorded game parsing and summarization in Python 3.

## Supported Versions

- Age of Kings (.mgl) [fast only]
- The Conquerors (.mgx) [fast only]
- Userpatch 1.4 (.mgz)
- Userpatch 1.5 (.mgz)
- Definitive Edition (.aoe2record)

## Examples

### Parser

```python
import os
from mgz import header, body

with open('/path/to/file', 'rb') as data:
    eof = os.fstat(data.fileno()).st_size
    header.parse_stream(data)
    body.meta.parse_stream(data)
    while data.tell() < eof:
        body.operation.parse_stream(data)
```

#### Fast Mode

Skips parsing most body operations for faster speed.

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
