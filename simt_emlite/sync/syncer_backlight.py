from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerBacklight(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        setting = self.emlite_client.backlight()
        return UpdatesTuple({"backlight": setting.name}, None)
