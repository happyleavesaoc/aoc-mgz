# mgz

AoC MGZ parsing in Python 2.x.

Usage:
 - Complete file:
   - mgz.parse(file)
 - Incomplete file (spec):
   - header.parse(file)
   - Loop: body.command.parse(file)

Caveats:
 - Parses only portions useful for multiplayer recorded game analysis
 - UserPatch 1.4 only

Dependencies:
 - construct: https://github.com/construct/construct

Contribution:
 - Pull requests & patches welcome

Resources:
 - aoc-mgx-format: https://github.com/stefan-kolb/aoc-mgx-format
 - node-aoe-rec: https://github.com/goto-bus-stop/node-aoe-rec
 - recanalyst: http://sourceforge.net/p/recanalyst/
