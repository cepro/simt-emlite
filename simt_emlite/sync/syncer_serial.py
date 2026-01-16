from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase
from simt_emlite.util.supabase import as_first_item

logger = get_logger(__name__, __file__)


class SyncerSerial(SyncerBase):
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

        is_3p = is_three_phase(as_first_item(result)["hardware"])
        serial = (
            self.emlite_client.three_phase_serial(self.serial)
            if is_3p
            else self.emlite_client.serial_read(self.serial)
        )

        # no change
        if serial == meter_registry_entry["serial"]:
            return UpdatesTuple(None, None)

        logger.info(
            "update serial",
            serial=serial,
        )
        return UpdatesTuple(None, {"serial": serial})
