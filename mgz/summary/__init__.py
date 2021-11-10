from mgz.fast.header import decompress, parse_version
from mgz.summary.full import FullSummary
from mgz.model.compat import ModelSummary
from mgz.util import Version


class SummaryStub:

    def __call__(self, data, playback=None, fallback=False):
        header = decompress(data)
        version, game, save, log = parse_version(header, data)
        data.seek(0)
        if version is Version.DE and save > 13.34 and not fallback:
            return ModelSummary(data, playback)
        return FullSummary(data, playback)


Summary = SummaryStub()


if __name__ == '__main__':
    for f in ['small.mgz', 'tests/recs/de-25.02.aoe2record', 'tests/recs/aoc-1.0c.mgx']:
        print('----------------')
        with open(f, 'rb') as h:
            ms = Summary(h)
        print(ms.get_players())
        #print(ms.get_mirror())
        #print(ms.get_platform())
