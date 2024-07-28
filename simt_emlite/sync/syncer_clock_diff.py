from datetime import datetime

from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


class SyncerClockDiff(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        clock_time: datetime = self.emlite_client.clock_time_read()

        now = datetime.utcnow()
        clock_time_diff_seconds = abs(now - clock_time).seconds
        logger.info(
            "clock_time_diff_seconds calculated",
            clock_time_diff_seconds=clock_time_diff_seconds,
        )

        return UpdatesTuple({"clock_time_diff_seconds": clock_time_diff_seconds}, None)
