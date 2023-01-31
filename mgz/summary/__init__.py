from mgz.fast.header import decompress, parse_version
from mgz.summary.full import FullSummary
from mgz.model.compat import ModelSummary
from mgz.util import Version
import logging
import zlib

logger = logging.getLogger(__name__)

class SummaryStub:

    def __call__(self, data, fallback=False):
        try:
            header = decompress(data)
            version, game, save, log = parse_version(header, data)
            data.seek(0)
            supported = (version is Version.DE and save > 13.34) # or version is Version.USERPATCH15
        except zlib.error:
            supported = False
        if supported and not fallback:
            logger.info("using model summary")
            try:
                return ModelSummary(data)
            except RuntimeError as e:
                logger.warning(f"could not fast parse; falling back: {e}")
        logger.info("using full summary")
        return FullSummary(data)


Summary = SummaryStub()
