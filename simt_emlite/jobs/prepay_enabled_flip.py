import argparse
import concurrent.futures
import os
import sys

from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")

meter_names_str = os.environ.get("PREPAY_DISABLED_METER_NAMES")
if meter_names_str is None:
    print('ERROR: PREPAY_DISABLED_METER_NAMES not defined')
    sys.exit(1)

meter_names = [name.strip() for name in meter_names_str.split(",")]
meter_names_len = len(meter_names)


"""
    Disable prepay enabled flags for given set of meters.
"""


class PrepayEnabledFlipJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        self.esco = esco
        self.containers = get_instance(esco=esco)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)

    def run_job(self, meter_row) -> bool:
        self.log.info(f"run_job for meter_row {meter_row}")
        return False
        # mediator_address = self.containers.mediator_address(meter_id, serial)
        # if mediator_address is None:
        #     self.log.error(f"No mediator container exists for meter {serial}")
        #     return False

        # try:
        #     self.log.info(
        #         "run_job",
        #         meter_id=meter_id,
        #         serial=serial,
        #         mediator_address=mediator_address,
        #     )

        #     job = FutureTariffsUpdateJob(
        #         tariff=tariff,
        #         mediator_address=mediator_address,
        #         supabase=self.backend_supabase,
        #     )

        #     return job.update()
        # except Exception as e:
        #     self.log.error(
        #         "Failure occurred pushing token",
        #         error=e,
        #         exception=traceback.format_exception(e),
        #     )
        #     return False

    def run(self):
        self.log.info("Starting prepay_enabled_flip job...")

        meters_result = (
            self.flows_supabase.table("meter_registry")
            .select("*")
            .in_("name", meter_names)
            .neq("prepay_enabled", False) # already disabled
            .execute()
        )

        if len(meters_result.data) == 0:
            self.log.error("No meter found to disable")
            sys.exit(10)

        meters_to_disable = meters_result.data
        self.log.info(f"Processing {len(meters_to_disable)} meters")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=5
        ) as executor:
            futures = [executor.submit(self.run_job, meter) for meter in meters_to_disable]

        results = concurrent.futures.wait(futures)

        success_count = 0
        for future in results.done:
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                self.log.error(f"Error processing meter: {e}")

        self.log.info(
            f"Finished prepay_enabled_flip job. Success: {success_count}/{len(meters_to_disable)}"
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
        help="Flip meters in this ESCO only",
    )
    args = parser.parse_args()

    esco = args.esco if hasattr(args, "esco") else None

    runner = PrepayEnabledFlipJob(esco=esco)
    runner.run()
