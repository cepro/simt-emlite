import inspect
import os
import sys
import traceback

from httpx import ConnectError

from simt_emlite import sync
from simt_emlite.jobs.util import check_environment_vars, handle_supabase_faliure
from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

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
        mediator_host: str = "0.0.0.0",
        mediator_port: str,
        supabase_url: str,
        supabase_key: str,
        flows_role_key: str,
        run_frequency: str,
    ):
        self.meter_id = meter_id
        self.mediator_host = mediator_host
        self.mediator_port = mediator_port
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.flows_role_key = flows_role_key
        self.run_frequency = run_frequency

        self.emlite_client = EmliteMediatorClient(
            port=self.mediator_port,
            mediator_host=self.mediator_host,
            meter_id=self.meter_id,
        )
        self.supabase = supa_client(
            self.supabase_url, self.supabase_key, self.flows_role_key
        )

        global logger
        self.log = logger.bind(meter_id=self.meter_id, mediator_port=self.mediator_port)

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

        for metric in query_result.data:
            syncer_class = find_syncer_class(metric["name"])
            syncer = syncer_class(self.supabase, self.emlite_client, self.meter_id)
            syncer.sync()


if __name__ == "__main__":
    meter_id: str = os.environ.get("METER_ID")

    mediator_host: str = os.environ.get("MEDIATOR_HOST") or "0.0.0.0"
    mediator_port: str = os.environ.get("MEDIATOR_PORT") or "50051"

    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_ANON_KEY")

    flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")

    check_environment_vars(logger, supabase_url, supabase_key, flows_role_key, meter_id)

    run_frequency: str = os.environ.get("RUN_FREQUENCY")
    if not run_frequency:
        logger.error("Environment variable RUN_FREQUENCY not set.")
        sys.exit(10)

    try:
        job = MeterSyncJob(
            meter_id=meter_id,
            mediator_host=mediator_host,
            mediator_port=mediator_port,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            flows_role_key=flows_role_key,
            run_frequency=run_frequency,
        )
        job.sync()
    except Exception as e:
        logger.error("failure occured syncing", error=e)
        traceback.print_exc()
