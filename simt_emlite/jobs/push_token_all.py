import argparse
import concurrent.futures
import os
import sys
import traceback

from simt_emlite.jobs.push_token import PushTokenJob
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")
public_backend_role_key: str = os.environ.get("PUBLIC_BACKEND_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)


"""
    Push tokens to meters for topups with "wait_token_push" status.
"""


class PushTokenAllJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        self.esco = esco
        self.containers = get_instance(esco)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.backend_supabase = supa_client(
            supabase_url, supabase_key, public_backend_role_key, schema="public"
        )

    def run_job(self, topup):
        topup_id = topup["id"]
        meter_id = topup["meter"]
        token = topup["token"]
        serial = topup["meters"]["serial"]  # Serial is in the nested meters object

        # Get meter details from meter_registry to find active meters
        meter_query = (
            self.flows_supabase.table("meter_registry")
            .select("*")
            .eq("serial", serial)
            .eq("mode", "active")
            .execute()
        )

        if len(meter_query.data) == 0:
            self.log.error(
                f"No active meter found in meter_registry with serial {serial}"
            )

            # Update topup status to failed
            self.backend_supabase.table("topups").update(
                {
                    "status": "failed_token_push",
                    "notes": "No active meter found in meter_registry",
                }
            ).eq("id", topup_id).execute()

            return False

        mediator_address = self.containers.mediator_address(meter_id, serial)
        if mediator_address is None:
            self.log.warn(f"No mediator container exists for meter {serial}")

            # Update topup status to failed
            self.backend_supabase.table("topups").update(
                {
                    "status": "failed_token_push",
                    "notes": "No mediator container available",
                }
            ).eq("id", topup_id).execute()

            return False

        try:
            self.log.info(
                "run_job",
                topup_id=topup_id,
                meter_id=meter_id,
                serial=serial,
                mediator_address=mediator_address,
            )

            job = PushTokenJob(
                topup_id=topup_id,
                meter_id=meter_id,
                token=token,
                mediator_address=mediator_address,
                supabase=self.backend_supabase,
            )

            return job.push()
        except Exception as e:
            self.log.error(
                "Failure occurred pushing token",
                error=e,
                exception=traceback.format_exception(e),
            )
            return False

    def run(self):
        self.log.info("Starting token push job...")

        # First query for topups with wait_token_push status
        if self.esco:
            # Get ESCO ID from name
            escos = (
                self.backend_supabase.table("escos")
                .select("id")
                .ilike("code", self.esco)
                .execute()
            )
            if len(escos.data) == 0:
                self.log.error("No esco found for " + self.esco)
                sys.exit(10)

            esco_id = list(escos.data)[0]["id"]

            # Query for topups at this ESCO with wait_token_push status with join to meters table
            topups_result = (
                self.backend_supabase.table("topups")
                .select("id, meter, token, status, meters(serial)")
                .eq("esco", esco_id)
                .eq("status", "wait_token_push")
                .is_("used_at", "null")
                .execute()
            )
        else:
            # Query all topups with wait_token_push status across all ESCOs
            topups_result = (
                self.backend_supabase.table("topups")
                .select("id, meter, token, status, meters(serial)")
                .eq("status", "wait_token_push")
                .is_("used_at", "null")
                .execute()
            )

        if len(topups_result.data) == 0:
            self.log.info("No pending topups found requiring token push")
            return

        topups = topups_result.data
        self.log.info(f"Found {len(topups)} topups requiring token push")

        # Extract all serials from topups
        topup_serials = {topup["meters"]["serial"] for topup in topups}

        # Now query meter_registry for active meters with matching serials
        active_meters_by_serial = {}
        for serial in topup_serials:
            meter_result = (
                self.flows_supabase.table("meter_registry")
                .select("id, serial")
                .eq("serial", serial)
                .eq("mode", "active")
                .execute()
            )
            if len(meter_result.data) > 0:
                active_meters_by_serial[serial] = meter_result.data[0]

        # Log any topups that don't have an active meter in meter_registry
        missing_serials = set()
        for topup in topups:
            serial = topup["meters"]["serial"]
            if serial not in active_meters_by_serial:
                missing_serials.add(serial)
                self.log.warn(
                    f"Topup {topup['id']} has no active meter {serial} in meter_registry",
                    serial=serial,
                    topup=topup["id"],
                )

        if missing_serials:
            self.log.warn(
                f"Found {len(missing_serials)} topups with no active meters: {list(missing_serials)}"
            )

        # Filter topups to only those with active meters
        valid_topups = [
            topup
            for topup in topups
            if topup["meters"]["serial"] in active_meters_by_serial
        ]

        if len(valid_topups) == 0:
            self.log.warn("No valid topups with active meters found")
            return

        self.log.info(f"Processing {len(valid_topups)} valid topups with active meters")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_parallel_jobs
        ) as executor:
            futures = [executor.submit(self.run_job, topup) for topup in valid_topups]

        results = concurrent.futures.wait(futures)

        success_count = sum(1 for future in results.done if future.result())

        self.log.info(
            f"Finished token push job. Success: {success_count}/{len(valid_topups)}"
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

        if not public_backend_role_key:
            self.log.error("Environment variable PUBLIC_BACKEND_ROLE_KEY not set.")
            sys.exit(4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--esco",
        action="store",
        help="Apply token push to meters in this ESCO only",
    )
    args = parser.parse_args()

    esco = args.esco if hasattr(args, "esco") else None

    runner = PushTokenAllJob(esco=esco)
    runner.run()
