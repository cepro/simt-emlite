from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase

logger = get_logger(__name__, __file__)


class SyncerReads(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple | None:
        result = (
            self.supabase.table("meter_registry")
            .select("hardware")
            .eq("id", self.meter_id)
            .execute()
        )

        is_3p = is_three_phase(result.data[0]["hardware"])
        if is_3p:
            # for now skip it but later we want to try do 3p reads
            return

        element_a_read = self.emlite_client.read_element_a()
        element_b_read = self.emlite_client.read_element_b()

        metrics = {
            "import_a": element_a_read.import_active,
            "import_b": element_b_read.import_active,
            "export_a": element_a_read.export_active,
            "export_b": element_b_read.export_active,
        }

        return UpdatesTuple(metrics, None)
