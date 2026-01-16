import unittest
from typing import Any, Dict, List
from unittest import skip
from unittest.mock import MagicMock, Mock, patch

from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple

"""
Inject '.return_value' strings into a function chain string for passing to
unittest's configure_mock() function.

eg. 'a.b.c' => 'a.return_value.b.return_value.c.side_effect'
"""


def fn_chain_str_with_ret_vals(chain: str):
    return chain.replace(".", ".return_value") + ".return_value"


class ASyncer(SyncerBase):
    def mock_responses(self, shadow_rec=None, registry_rec=None):
        self.shadow_rec = shadow_rec
        self.registry_rec = registry_rec

    @override
    def fetch_metrics(self) -> UpdatesTuple:
        return UpdatesTuple(self.shadow_rec, self.registry_rec)


class MockAPIResponse:
    data: List[Dict[str, Any]]

    def __init__(self, dict):
        self.dict = dict


class TestSyncerBase(unittest.TestCase):
    def test_no_instantiate(self):
        with self.assertRaises(TypeError) as cm:
            SyncerBase()
        self.assertIn("Can't instantiate abstract class", str(cm.exception))

    def test_sync_single_metric_to_shadows(self):
        with patch("supabase.Client") as supabase:
            mock_table_execute = Mock()
            mock_table_execute.configure_mock(
                **{
                    # mock the meter_shadows update
                    fn_chain_str_with_ret_vals("update.eq.execute"): {}
                }
            )
            supabase.table = mock_table_execute

            syncer = ASyncer(
                supabase, emlite_client=None, meter_id="123", serial="TEST_SERIAL"
            )
            syncer.mock_responses(shadow_rec={"csq": 20}, registry_rec=None)
            syncer.sync()

            mock_table_execute.return_value.update.assert_called_with(
                {"csq": 20, "health": "healthy", "health_details": ""}
            )

    @skip(reason="unable to get the MockAPIResponse returning below - TODO revsit this")
    def test_sync_single_metric_to_register_new_value(self):
        with patch("supabase.Client") as supabase:
            mock_table_execute = MagicMock()
            mock_table_execute.configure_mock(
                **{
                    # query meter_registry for current record (before update)
                    fn_chain_str_with_ret_vals(
                        "select.join.eq.execute"
                    ): MockAPIResponse([{"serial": None}]),
                    # mock the meter_registry update
                    fn_chain_str_with_ret_vals("update.eq.execute"): {},
                }
            )
            supabase.table = mock_table_execute

            syncer = ASyncer(
                supabase, emlite_client=None, meter_id="123", serial="TEST_SERIAL"
            )
            syncer.mock_responses(shadow_rec=None, registry_rec={"serial": "EML12345"})
            syncer.sync()

            mock_table_execute.return_value.update.assert_called_with(
                {"serial": "EML12345"}
            )
