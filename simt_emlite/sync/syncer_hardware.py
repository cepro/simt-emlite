from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

single_phase_hardware_str_to_registry_str = {
    "6C": "C1.w",
    "6Cw": "C1.w",
    "6Bw": "B1.w",
    "3Aw": "EMA1.w",
}

three_phase_hardware_known_strings = ["P1.ax", "P1.cx", "THREE_PHASE_UNKNOWN"]


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

        hardware_rsp = self.emlite_client.hardware()

        if hardware_rsp not in three_phase_hardware_known_strings:
            hardware = single_phase_hardware_str_to_registry_str[hardware_rsp]
            if hardware is None:
                hardware = "SINGLE_PHASE_UNKNOWN"
        else:
            hardware = hardware_rsp

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
