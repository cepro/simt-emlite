from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerPrepayBalance(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        balance = self.emlite_client.prepay_balance()
        return UpdatesTuple({'balance': balance}, None)
