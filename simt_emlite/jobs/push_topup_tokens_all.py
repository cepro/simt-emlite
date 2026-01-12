import argparse
import concurrent.futures
import os
import sys
import traceback

from simt_emlite.jobs.push_topup_token import PushTopupTokenJob
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
public_backend_role_key: str | None = os.environ.get("PUBLIC_BACKEND_ROLE_KEY")
max_parallel_jobs: int | None = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)
env: str | None = os.environ.get("ENV")


"""
    Push tokens to meters for topups with "wait_token_push" status.
"""


class PushTopupTokensAllJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        # Narrow types after environment check
        assert supabase_url is not None
        assert supabase_key is not None

        self.esco = esco
        self.containers = get_instance(esco=esco, env=env)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.backend_supabase = supa_client(
            supabase_url, supabase_key, public_backend_role_key, schema="myenergy"
        )

    def run_job(self, topup):
        topup_id = topup["id"]
        token = topup["token"]
        serial = topup["meters"]["serial"]  # Serial is in the nested meters object

        # look up meter in the flows meter_registry checking it's active
        meter_query = (
            self.flows_supabase.table("meter_registry")
            .select("*")
            .eq("serial", serial)
            .eq("mode", "active")
            .execute()
        )

        if len(as_list(meter_query)) == 0:
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

        meter_id = as_first_item(meter_query)["id"]

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

            job = PushTopupTokenJob(
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

    def run(self, status: str = "wait_token_push"):
        self.log.info("Starting token push job...")

        # query for topups with wait_token_push status
        if self.esco:
            # Get ESCO ID from name
            escos = (
                self.backend_supabase.table("escos")
                .select("id")
                .ilike("code", self.esco)
                .execute()
            )
            if len(as_list(escos)) == 0:
                self.log.error("No esco found for " + self.esco)
                sys.exit(10)
            esco_id = as_first_item(escos)["id"]

            # all supply meters filtered by ESCO
            supply_meters_result = (
                self.backend_supabase.table("properties")
                .select("supply_meter")
                .eq("esco", esco_id)
                .execute()
            )
            supply_meters_for_esco = list(
                map(lambda m: m["supply_meter"], as_list(supply_meters_result))
            )

            # topups in wait_token_push status for supply meters in esco
            topups_result = self._get_topups_query(status, supply_meters_for_esco)
        else:
            # Query all topups with status across all ESCOs
            topups_result = self._get_topups_query(status)

        if len(as_list(topups_result)) == 0:
            self.log.info(f"No topups in status {status}")
            return

        topups = as_list(topups_result)
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
            if len(as_list(meter_result)) > 0:
                active_meters_by_serial[serial] = as_first_item(meter_result)

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

    def _get_topups_query(self, status: str, meters: list[str] | None = None):
        """Query topups table with optional meter filter"""
        query = (
            self.backend_supabase.table("topups")
            .select("id, meter, token, status, meters(serial)")
            .eq("status", status)
            .is_("used_at", "null")
        )

        if meters:
            query = query.in_("meter", meters)

        return query.execute()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--esco",
        action="store",
        help="Apply token push to meters in this ESCO only",
    )
    args = parser.parse_args()

    esco = args.esco if hasattr(args, "esco") else None

    runner = PushTopupTokensAllJob(esco=esco)
    runner.run("wait_token_push")
    runner.run("failed_token_push")
