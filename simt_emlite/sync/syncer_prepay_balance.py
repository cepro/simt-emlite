from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase

logger = get_logger(__name__, __file__)


class SyncerPrepayBalance(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = (
            self.supabase.table("meter_registry")
            .select("prepay_enabled, hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        # skip prepay metrics on 3phase meters - properties don't exist so emop calls fail
        if is_three_phase(result.data[0]["hardware"]):
            return None

        enabled = result.data[0]["prepay_enabled"]
        if enabled is not True:
            logger.info(
                "prepay not enabled, skipping balance lookup ...",
                meter_id=self.meter_id,
            )
            return None

        balance = self.emlite_client.prepay_balance()
        return UpdatesTuple({"balance": str(balance)}, None)
