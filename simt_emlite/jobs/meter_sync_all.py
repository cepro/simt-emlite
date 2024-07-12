import argparse
import concurrent.futures
import os
import sys
import traceback
from typing import Any, Callable

from simt_emlite.jobs.meter_sync import MeterSyncJob
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 15)


def filter_connected(meter):
    return meter["ip_address"] is not None


"""
    Run the meter sync job for all meters in a given esco.
"""


class MeterSyncAllJob:
    def __init__(
        self,
        filter_fn: Callable[[Any], bool] = None,
        run_frequency=None,
        esco=None,
    ):
        self._check_environment()
        self.filter_fn = filter_fn
        self.supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.containers = get_instance(esco)
        self.run_frequency = run_frequency
        self.esco = esco

        global logger
        self.log = logger.bind(esco=self.esco)

    def run_job(self, meter_id, serial):
        mediator_host, mediator_port = self.containers.mediator_address(
            meter_id, serial
        )
        if mediator_port is None or mediator_host is None:
            self.log.warn(f"no mediator container exists for meter {serial}")
            return

        try:
            self.log.info(
                "run_job",
                meter_id=meter_id,
                mediator_host=mediator_host,
                mediator_port=mediator_port,
            )
            job = MeterSyncJob(
                meter_id=meter_id,
                mediator_host=mediator_host,
                mediator_port=mediator_port,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                flows_role_key=flows_role_key,
                run_frequency=self.run_frequency,
            )
            job.sync()
        except Exception as e:
            self.log.error("failure occured syncing", error=e)
            traceback.print_exc()

    def run(self):
        self.log.info("starting ...")

        escos = (
            self.supabase.table("escos").select("id").ilike("code", self.esco).execute()
        )
        if len(escos.data) == 0:
            self.log.error("no esco found for " + self.esco)
            sys.exit(10)

        esco_id = list(escos.data)[0]["id"]

        registry_result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address,serial,hardware")
            # only process meters at the given esco
            .eq("esco", esco_id)
            # only sync active / real hardware meters
            # passive meters are synced from active meters in
            #   some other database and environment
            .eq("mode", "active")
            .order(column="serial")
            .execute()
        )
        if len(registry_result.data) == 0:
            self.log.error("no meters record found")
            sys.exit(11)

        meters = list(filter(filter_connected, registry_result.data))
        if self.filter_fn:
            meters = list(filter(self.filter_fn, meters))

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_parallel_jobs
        ) as executor:
            futures = [
                executor.submit(self.run_job, meter["id"], meter["serial"])
                for meter in meters
            ]

        concurrent.futures.wait(futures)

        self.log.info("finished")

    def _check_environment(self):
        if not supabase_url or not supabase_key:
            self.log.error(
                "Environment variables SUPABASE_URL and SUPABASE_ANON_KEY not set."
            )
            sys.exit(2)

        if not flows_role_key:
            self.log.error("Environment variable FLOWS_ROLE_KEY not set.")
            sys.exit(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freq",
        required=True,
        action="store",
        choices=["hourly", "daily", "12hourly"],
        help="Sync meter_metrics that have this frequency",
    )
    parser.add_argument(
        "--esco",
        required=True,
        action="store",
        help="Apply sync to meters in this esco only",
    )
    args = parser.parse_args()

    freq = args.freq
    esco = args.esco

    runner = MeterSyncAllJob(run_frequency=freq, esco=esco)
    runner.run()
