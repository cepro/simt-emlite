from emlite_mediator.util.logging import get_logger

from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple

logger = get_logger(__name__, __file__)


class SyncerPrepayBalance(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = self.supabase.table('meter_registry').select(
            'prepay_enabled').eq("id", self.meter_id).execute()
        enabled = result.data[0]['prepay_enabled']
        if enabled != True:
            logger.info('prepay not enabled, skipping balance lookup ...',
                        meter_id=self.meter_id)
            return None

        balance = self.emlite_client.prepay_balance()
        return UpdatesTuple({'balance': balance}, None)
