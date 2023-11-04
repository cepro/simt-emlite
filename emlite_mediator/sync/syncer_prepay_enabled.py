from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerPrepayEnabled(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        prepay_enabled = self.emlite_client.prepay_enabled()
        return UpdatesTuple(None, {'prepay_enabled': prepay_enabled})
