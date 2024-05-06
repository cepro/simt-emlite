from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerCsq(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        csq = self.emlite_client.csq()
        return UpdatesTuple({'csq': csq}, None)
