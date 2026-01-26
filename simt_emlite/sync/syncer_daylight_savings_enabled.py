from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.meters import is_three_phase
from simt_emlite.util.supabase import as_first_item


class SyncerDaylightSavingsEnabled(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = (
            self.supabase.table("meter_registry")
            .select("hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        # skip on 3phase meters - properties don't exist so emop calls fail
        if is_three_phase(as_first_item(result)["hardware"]):
            return UpdatesTuple(None, None)

        enabled = self.emlite_client.daylight_savings_correction_enabled(self.serial)
        return UpdatesTuple(
            None,
            {"daylight_savings_correction_enabled": enabled},
        )
