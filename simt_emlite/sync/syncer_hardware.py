from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import as_first_item

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
        if len(result.data) == 0:
            raise ValueError(f"Meter not found with id {self.meter_id}")
        meter_registry_entry = as_first_item(result)

        hardware = self.emlite_client.hardware(self.serial)

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
