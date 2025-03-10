from emop_frame_protocol.emop_message import EmopMessage
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase_lookup

logger = get_logger(__name__, __file__)


class SyncerLoadSwitch(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            return

        setting = self.emlite_client.load_switch()

        if not isinstance(setting, EmopMessage.LoadSwitchSettingType):
            logger.warn("skipping because the load_switch value is unknown")
            return

        return UpdatesTuple({"load_switch": setting.name}, None)
