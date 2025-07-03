from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.meters import is_three_phase_lookup


class SyncerTariffsActive(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            return UpdatesTuple(None, None)

        tariffs = self.emlite_client.tariffs_active_read()
        return UpdatesTuple({"tariffs_active": tariffs}, None)
