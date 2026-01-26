import inspect
import traceback

from httpx import ConnectError

from simt_emlite import sync
from simt_emlite.jobs.util import handle_supabase_faliure
from simt_emlite.mediator.api_core import EmliteMediatorAPI
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

logger = get_logger(__name__, __file__)


def find_syncer_class(name):
    sync_members = inspect.getmembers(sync)
    matches = list(
        filter(
            lambda member: member[0] == name,
            sync_members,
        )
    )
    return matches[0][1] if len(matches) == 1 else None


"""
    Sync meter metrics to the shadow table.
"""


class MeterSyncJob:
    def __init__(
        self,
        *,
        meter_id: str,
        mediator_address: str = "0.0.0.0:50051",
        supabase_url: str,
        supabase_key: str,
        flows_role_key: str,
        run_frequency: str,
        use_cert_auth: bool = False,
    ):
        self.meter_id = meter_id
        self.mediator_address = mediator_address
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.flows_role_key = flows_role_key
        self.run_frequency = run_frequency

        self.supabase = supa_client(
            self.supabase_url, self.supabase_key, self.flows_role_key
        )

        # Look up meter details by meter_id
        result = (
            self.supabase.table("meter_registry")
            .select("serial")
            .eq("id", self.meter_id)
            .execute()
        )
        if len(as_list(result)) == 0:
            raise Exception(f"meter {self.meter_id} not found")

        self.serial = as_first_item(result)["serial"]

        self.emlite_client = EmliteMediatorAPI(
            mediator_address=mediator_address,
        )

        global logger
        self.log = logger.bind(
            meter_id=self.meter_id, mediator_address=self.mediator_address
        )

    def sync(self):
        try:
            query_result = (
                self.supabase.table("meter_metrics")
                .select("*")
                .eq("enabled", True)
                .eq("run_frequency", self.run_frequency)
                .execute()
            )
        except ConnectError as e:
            handle_supabase_faliure(self.log, e)
            return

        for metric in as_list(query_result):
            try:
                syncer_class = find_syncer_class(metric["name"])
                syncer = syncer_class(self.supabase, self.emlite_client, self.meter_id, self.serial)
                syncer.sync()
            except Exception as e:
                self.log.error(
                    f"failure occurred syncing metric {metric['name']}",
                    error=e,
                    exception=traceback.format_exception(e),
                )
