from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase_lookup

logger = get_logger(__name__, __file__)


class SyncerVoltage(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            (v1, v2, v3) = self.emlite_client.three_phase_instantaneous_voltage(self.serial)
            metrics = {"3p_voltage_l1": v1, "3p_voltage_l2": v2, "3p_voltage_l3": v3}
        else:
            voltage = self.emlite_client.instantaneous_voltage(self.serial)
            metrics = {"voltage": voltage}

        return UpdatesTuple(metrics, None)
