from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerTariffsActive(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        tariffs = self.emlite_client.tariffs_active_read()
        return UpdatesTuple({"tariffs_active": tariffs}, None)
