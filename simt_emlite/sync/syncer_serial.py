from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

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
        meter_registry_entry = result.data[0]

        serial = (
            self.emlite_client.three_phase_serial()
            if meter_registry_entry["hardware"] == "P1.ax"
            else self.emlite_client.serial()
        )

        # no change
        if serial == meter_registry_entry["serial"]:
            return UpdatesTuple(None, None)

        logger.info(
            "update serial",
            serial=serial,
        )
        return UpdatesTuple(None, {"serial": serial})
