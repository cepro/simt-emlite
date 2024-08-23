from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.meters import is_three_phase


class SyncerDaylightSavingsEnabled(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = (
            self.supabase.table("meter_registry")
            .select("hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        # skip on 3phase meters - properties don't exist so emop calls fail
        if is_three_phase(result.data[0]["hardware"]):
            return None

        enabled = self.emlite_client.daylight_savings_correction_enabled()
        return UpdatesTuple(
            None,
            {"daylight_savings_correction_enabled": enabled},
        )
