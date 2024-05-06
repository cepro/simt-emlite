from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


class SyncerFirmwareVersion(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = (
            self.supabase.table("meter_registry")
            .select("firmware_version,serial")
            .eq("id", self.meter_id)
            .execute()
        )
        meter_registry_entry = result.data[0]

        current_firmware_version = self.emlite_client.firmware_version()

        registry_firmware_version = meter_registry_entry["firmware_version"]
        if registry_firmware_version == current_firmware_version:
            return UpdatesTuple(None, None)

        logger.info(
            "update firmware_version",
            new_firmware_version=current_firmware_version,
        )

        return UpdatesTuple(None, {"firmware_version": current_firmware_version})
