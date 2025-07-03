from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase_lookup

logger = get_logger(__name__, __file__)


class SyncerReads(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            # for now skip it but later we want to try do 3p reads
            return UpdatesTuple(None, None)

        element_a_read = self.emlite_client.read_element_a()
        element_b_read = self.emlite_client.read_element_b()

        metrics = {
            "import_a": element_a_read.import_active,
            "import_b": element_b_read.import_active,
            "export_a": element_a_read.export_active,
            "export_b": element_b_read.export_active,
        }

        return UpdatesTuple(metrics, None)
