from emop_frame_protocol.emop_message import EmopMessage
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


class SyncerBacklight(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        setting = self.emlite_client.backlight()

        if not isinstance(setting, EmopMessage.BacklightSettingType):
            logger.warn(
                "skipping because the backlight value is not of type BacklightSettingType - likely a three phase meter"
            )
            return

        return UpdatesTuple({"backlight": setting.name}, None)
