from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerSerial(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        serial = self.emlite_client.serial()
        return UpdatesTuple(None, {'serial': serial})
