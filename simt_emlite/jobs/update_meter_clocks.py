import argparse
import concurrent.futures
import datetime
import os
import sys
import traceback
from typing import Dict

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.mediator.mediator_client_exception import MediatorClientException
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)
drift_threshold_seconds: int = int(os.environ.get("DRIFT_THRESHOLD_SECONDS") or 20)
env: str | None = os.environ.get("ENV")



"""
    Update clock_time_write for any meters that have drifted more than DRIFT_THRESHOLD_SECONDS seconds.
"""


class UpdateMeterClocksJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        # Narrow types after environment check
        assert supabase_url is not None
        assert supabase_key is not None
        assert flows_role_key is not None

        self.esco = esco
        self.containers = get_instance(esco=esco, env=env)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)

    def run_job(self, meter_drift_record: Dict):
        serial = meter_drift_record["serial"]
        drift_seconds = meter_drift_record["clock_time_diff_seconds"]
        meter_id = meter_drift_record["id"]

        mediator_address = self.containers.mediator_address(meter_id, serial)
        if mediator_address is None:
            self.log.error(f"No mediator container exists for meter {serial}")
            return False

        try:
            self.log.info(
                "Updating clock",
                meter_id=meter_id,
                serial=serial,
                mediator_address=mediator_address,
                drift_seconds=drift_seconds,
            )

            client = EmliteMediatorClient(
                mediator_address=mediator_address,
                meter_id=meter_id,
            )

            # Write the correct time
            client.clock_time_write()

            # 2. Reset clock drift in meter_shadows now that it's synced
            self.flows_supabase.table("meter_shadows").update(
                {
                    "clock_time_diff_seconds": 0,
                    "clock_time_diff_synced_at": datetime.datetime.now(
                        datetime.UTC
                    ).isoformat(),
                }
            ).eq("id", meter_id).execute()

            self.log.info("Clock update successful", serial=serial)
            return True

        except MediatorClientException as e:
            if e.code_str == "DEADLINE_EXCEEDED":
                self.log.error(
                    "Deadline exceeded updating clock",
                    serial=serial,
                    error=str(e),
                )
            else:
                self.log.error(
                    "Mediator client error updating clock",
                    serial=serial,
                    error=e,
                    exception=traceback.format_exception(e),
                )
            return False
        except Exception as e:
            self.log.error(
                "Failure occurred updating clock",
                serial=serial,
                error=e,
                exception=traceback.format_exception(e),
            )
            return False

    def run(self):
        self.log.info("Starting update meter clocks job...")

        try:
            # Query meter_shadows, joining meter_registry and escos to allow filtering by code
            select_str = "clock_time_diff_seconds, id, meter_registry!inner(serial, mode"
            if self.esco:
                select_str += ", escos!inner(code)"
            select_str += ")"

            query = (
                self.flows_supabase.table("meter_shadows")
                .select(select_str)
                .gt("clock_time_diff_seconds", drift_threshold_seconds)
                .eq("meter_registry.mode", "active")
            )

            if self.esco:
                query = query.eq("meter_registry.escos.code", self.esco)

            response = query.execute()
            self.log.info("Raw database response", data=response.data)
        except Exception as e:
            self.log.error("Failed to query meter_shadows", error=e)
            sys.exit(1)

        # Python post-check filtering as esco filtering in Supabase might be failing
        records = response.data
        if self.esco:
            records = [
                r
                for r in records
                if r.get("meter_registry", {}).get("escos", {}).get("code") == self.esco
            ]
            self.log.info(
                f"Post-filtered by esco {self.esco}",
                original_count=len(response.data),
                filtered_count=len(records),
            )

        drifted_meters = [
            {
                "id": record["id"],
                "serial": record["meter_registry"]["serial"],
                "clock_time_diff_seconds": record["clock_time_diff_seconds"],
            }
            for record in records
        ]
        self.log.info(
            f"Found {len(drifted_meters)} meters with clock drift > {drift_threshold_seconds}s",
            drifted_meters=drifted_meters,
        )

        if len(drifted_meters) == 0:
            self.log.info("No meters to update.")
            return

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_parallel_jobs
        ) as executor:
            futures = [executor.submit(self.run_job, record) for record in drifted_meters]

        results = concurrent.futures.wait(futures)
        success_count = sum(1 for future in results.done if future.result())

        self.log.info(
            f"Finished clock update job. Success: {success_count}/{len(drifted_meters)}"
        )

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
        "--esco",
        action="store",
        help="Apply clock updates to meters in this ESCO only",
    )
    args = parser.parse_args()

    esco = args.esco if hasattr(args, "esco") else None

    runner = UpdateMeterClocksJob(esco=esco)
    runner.run()
