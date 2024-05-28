from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


class SyncerVoltage(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = (
            self.supabase.table("meter_registry")
            .select("serial")
            .eq("id", self.meter_id)
            .execute()
        )
        serial = result.data[0]["serial"]
        if serial is None:
            logger.info("no serial yet for meter, skipping ...", meter_id=self.meter_id)
            return None

        is_3p = serial.startswith("EMP1AX")
        if is_3p:
            (v1, v2, v3) = self.emlite_client.three_phase_instantaneous_voltage()
            metrics = {"3p_voltage_l1": v1, "3p_voltage_l2": v2, "3p_voltage_l3": v3}
        else:
            voltage = self.emlite_client.instantaneous_voltage()
            metrics = {"voltage": voltage}

        return UpdatesTuple(metrics, None)
