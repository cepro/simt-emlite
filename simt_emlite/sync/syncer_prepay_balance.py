from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase
from simt_emlite.util.supabase import as_first_item

logger = get_logger(__name__, __file__)


class SyncerPrepayBalance(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = (
            self.supabase.table("meter_registry")
            .select("prepay_enabled, hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        # skip prepay metrics on 3phase meters - properties don't exist so emop calls fail
        if is_three_phase(as_first_item(result)["hardware"]):
            return UpdatesTuple(None, None)

        balance = self.emlite_client.prepay_balance()
        return UpdatesTuple({"balance": str(balance)}, None)
