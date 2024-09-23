from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerTariffsFuture(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        tariffs = self.emlite_client.tariffs_future_read()
        return UpdatesTuple({"tariffs_future": tariffs}, None)
