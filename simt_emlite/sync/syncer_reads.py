from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import get_hardware, is_three_phase_lookup

logger = get_logger(__name__, __file__)


class SyncerReads(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        # skip until we know the hardware type
        hardware = get_hardware(self.supabase, self.meter_id)
        if hardware is None or hardware == "":
            return UpdatesTuple(None, None)

        # skip until we implement 3p reads
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            three_phase_read = self.emlite_client.three_phase_read(self.serial, hardware=None)
            metrics = {
                "import_a": three_phase_read["active_import"],
                "import_b": three_phase_read["active_export"],
            }
            return UpdatesTuple(metrics, None)

        element_a_read = self.emlite_client.read_element_a(self.serial)
        element_b_read = self.emlite_client.read_element_b(self.serial)

        metrics = {
            "import_a": element_a_read["import_active"],
            "import_b": element_b_read["import_active"],
            "export_a": element_a_read["export_active"],
            "export_b": element_b_read["export_active"],
        }

        return UpdatesTuple(metrics, None)
