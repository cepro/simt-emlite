from typing_extensions import override
import unittest
from unittest.mock import Mock, patch

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple


class ASyncer(SyncerBase):
    def mock_responses(self, shadow_rec=None, registry_rec=None):
        self.shadow_rec = shadow_rec
        self.registry_rec = registry_rec

    @override
    def fetch_metrics(self) -> UpdatesTuple:
        return UpdatesTuple(self.shadow_rec, self.registry_rec)


class TestSyncerBase(unittest.TestCase):
    def test_no_instantiate(self):
        with self.assertRaises(TypeError) as cm:
            SyncerBase()
        self.assertIn("Can't instantiate abstract class", str(cm.exception))

    def test_sync_single_metric_to_shadows(self):
        with patch('supabase.Client') as supabase:
            mock_table_config = {
                'update.return_value.eq.return_value.execute.return_value': {}
            }
            mock_table = Mock()
            mock_table.configure_mock(**mock_table_config)
            supabase.table = mock_table

            test_syncer = ASyncer(supabase, emlite_client=None, meter_id='123')
            test_syncer.mock_responses(
                shadow_rec={"csq": 20}, registry_rec=None)
            test_syncer.sync()

            mock_table.return_value.update.assert_called_with(
                {'csq': 20, 'health': 'healthy', 'health_details': ''})
