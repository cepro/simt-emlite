from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.meters import is_three_phase


class SyncerPrepayEnabled(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = (
            self.supabase.table("meter_registry")
            .select("hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        # skip prepay metrics on 3phase meters - properties don't exist so emop calls fail
        if is_three_phase(result.data[0]["hardware"]):
            return UpdatesTuple(None, None)

        prepay_enabled = self.emlite_client.prepay_enabled()
        return UpdatesTuple(None, {"prepay_enabled": prepay_enabled})
