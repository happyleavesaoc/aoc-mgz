import sys
import pprint
from mgz.recorded_game import RecordedGame

if __name__ == "__main__":
    game = RecordedGame(sys.argv[1])
    pp = pprint.PrettyPrinter(indent=4)
    for op in game.operations(op_types=['message']):
        print(op)
    pp.pprint(game.summarize())
