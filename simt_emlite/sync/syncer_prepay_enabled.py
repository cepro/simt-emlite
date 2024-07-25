from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerPrepayEnabled(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = (
            self.supabase.table("meter_registry")
            .select("serial")
            .eq("id", self.meter_id)
            .execute()
        )
        serial = result.data[0]["serial"]
        is_3phase = serial.startswith("EMP1AX")

        # skip prepay metrics on 3phase meters - properties don't exist so emop calls fail
        if is_3phase:
            return None

        prepay_enabled = self.emlite_client.prepay_enabled()
        return UpdatesTuple(None, {"prepay_enabled": prepay_enabled})
