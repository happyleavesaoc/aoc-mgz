# mgz

AoC MGZ parsing in Python 3.

### Usage
 - header.parse_stream(file)
 - Loop: body.command.parse_stream(file)
 - Handle your own buffering

### Caveats
 - Parses only portions useful for multiplayer recorded game analysis
 - UserPatch 1.4, 1.5 only

### Dependencies
 - construct: https://github.com/construct/construct

### Improvements Needed
 - Parse objects fully (units, buildings, etc)
 - Enum expansion
 - Support for previous versions
 - Resolve unknown bytes

### Contribution
 - Pull requests & patches welcome

### Resources
 - aoc-mgx-format: https://github.com/stefan-kolb/aoc-mgx-format
 - recage: https://github.com/goto-bus-stop/recage
 - recanalyst: http://sourceforge.net/p/recanalyst/
 - bari-mgx-format: https://web.archive.org/web/20090215065209/http://members.at.infoseek.co.jp/aocai/mgx_format.html

### Output

General format of the file, noting interesting parts.
- Header
  - Version
  - AI
  - Record properties
    - Speed
    - Number of players
    - View of
  - Map
    - Size
    - Tiles
  - State
    - Start time
    - Players[]
      - Name
      - Diplomacy
      - Civilization
      - Color
      - Camera
      - Objects[]
        - Type
        - ID
        - Position
  - Achievements[]
  - Scenario
    - Instructions
    - Victory condition
    - Map type
    - Difficulty
    - Triggers
  - Lobby
    - Teams
    - Reveal map
    - Population limit
    - Game type
    - Lock diplomacy
    - Pre-game chat
- Body
  - Commands[]
     - Sync, Message, or Action
