# mypy: disable-error-code="import-untyped"
from emop_frame_protocol.emop_message import EmopMessage
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase_lookup

logger = get_logger(__name__, __file__)


class SyncerBacklight(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        setting = self.emlite_client.backlight(self.serial)

        if not isinstance(setting, EmopMessage.BacklightSettingType):
            logger.warn("skipping because the backlight value is unknown")
            return UpdatesTuple(None, None)

        setting_name = setting.name

        # for the setting shared by single phase and three phase - convert
        # to a name that is specific:
        if (
            setting_name
            == EmopMessage.BacklightSettingType.normal_sp_or_always_off_3p.name
        ):
            is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
            setting_name = "always_off_3p" if is_3p else "normal_sp"

        return UpdatesTuple({"backlight": setting_name}, None)
