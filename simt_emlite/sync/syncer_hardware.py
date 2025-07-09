from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


class SyncerHardware(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = (
            self.supabase.table("meter_registry")
            .select("hardware,serial")
            .eq("id", self.meter_id)
            .execute()
        )
        meter_registry_entry = result.data[0]

        hardware = self.emlite_client.hardware()

        registry_hardware = meter_registry_entry["hardware"]
        if registry_hardware == hardware:
            return UpdatesTuple(None, None)

        if registry_hardware is None and hardware is not None:
            logger.info("got new hardware", new_hardware=hardware)
        else:
            logger.warning(
                "fetched hardware and registry hardware different!",
                new_hardware=hardware,
                old_hardware=registry_hardware,
            )

        return UpdatesTuple(None, {"hardware": hardware})
