from mgz.fast.header import decompress, parse_version
from mgz.summary.full import FullSummary
from mgz.model.compat import ModelSummary
from mgz.util import Version
import logging

logger = logging.getLogger(__name__)

class SummaryStub:

    def __call__(self, data, playback=None, fallback=False):
        header = decompress(data)
        version, game, save, log = parse_version(header, data)
        data.seek(0)
        if version is Version.DE and save > 13.34 and not fallback:
            logger.info("using model summary")
            try:
                return ModelSummary(data, playback)
            except RuntimeError:
                logger.warning("could not fast parse; falling back")
        logger.info("using full summary")
        return FullSummary(data, playback)


Summary = SummaryStub()
