# mgz

Age of Empires II recorded game parsing and summarization in Python 3.

## Supported Versions

- Userpatch 1.4 (.mgz)
- Userpatch 1.5 (.mgz)
- Definitive Edition (.aoe2record)

## Examples

### Parser

```python
from mgz import header, body

with open('/path/to/file', 'rb') as data:
    eof = os.fstat(data.fileno()).st_size
    header.parse_stream(data)
    while data.tell() < eof:
        body.operation.parse_stream(data)
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

## Contribution
 - Pull requests & patches welcome

## Resources
 - aoc-mgx-format: https://github.com/stefan-kolb/aoc-mgx-format
 - recage: https://github.com/goto-bus-stop/recage
 - recanalyst: http://sourceforge.net/p/recanalyst/
 - bari-mgx-format: https://web.archive.org/web/20090215065209/http://members.at.infoseek.co.jp/aocai/mgx_format.html
