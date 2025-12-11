import argparse
import concurrent.futures
import os
import sys
import traceback
from typing import Any, Dict

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.mediator.mediator_client_exception import (
    MediatorClientException,
)
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import Client as SupabaseClient
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
env: str | None = os.environ.get("ENV")


class PrepayEnabledFlipJob:
    def __init__(
        self,
        *,
        meter: Dict[str, Any],
        mediator_address: str,
        supabase: SupabaseClient,
    ):
        self.meter = meter
        self.mediator_address = mediator_address
        self.supabase = supabase

        self.emlite_client = EmliteMediatorClient(
            mediator_address=mediator_address,
            meter_id=meter["id"],
        )

        global logger
        self.log = logger.bind(
            serial=meter["serial"],
            meter_id=meter["id"],
            mediator_address=mediator_address,
        )

    def update(self) -> bool:
        """
        Update the prepay_enabled flag on the meter.
        Returns True if successful, False if failed.
        """

        try:
            self.emlite_client.prepay_enabled_write(False)
            self.log.info("prepay disabled")
            return True
        except MediatorClientException as e:
            self.log.error(
                "Mediator client failure",
                error=e,
                exception=traceback.format_exception(e),
            )
        except Exception as e:
            self.log.error(
                "Unknown failure during prepay_enabled flag disable",
                error=e,
                exception=traceback.format_exception(e),
            )

        return False


"""
    Disable prepay enabled flags for given set of meters.
"""


class PrepayEnabledFlipAllJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        self.esco = esco
        self.containers = get_instance(esco=esco, env=env)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)

    def run_job(self, meter_row) -> bool:
        self.log.info(f"run_job for meter_row {meter_row}")

        meter_id = meter_row["id"]
        serial = meter_row["serial"]

        mediator_address = self.containers.mediator_address(meter_id, serial)
        if mediator_address is None:
            self.log.error(f"No mediator container exists for meter {serial}")
            return False

        try:
            self.log.info(
                "run_job",
                meter_id=meter_id,
                serial=serial,
                mediator_address=mediator_address,
            )

            job = PrepayEnabledFlipJob(
                meter=meter_row,
                mediator_address=mediator_address,
                supabase=self.flows_supabase,
            )

            return job.update()
        except Exception as e:
            self.log.error(
                "Failure occurred pushing token",
                error=e,
                exception=traceback.format_exception(e),
            )
            return False

    def run(self):
        self.log.info("Starting prepay_enabled_flip job...")

        escos = (
            self.supabase.table("escos").select("id").ilike("code", self.esco).execute()
        )
        if len(escos.data) == 0:
            self.log.error("no esco found for " + self.esco)
            sys.exit(10)

        esco_id = list(escos.data)[0]["id"]

        meters_result = (
            self.flows_supabase.table("meter_registry")
            .select("*")
            .eq("esco_id", esco_id)
            .eq("prepay_enabled", True)
            .neq("hardware", "P1.ax")
            .neq("hardware", "P1.cx")
            .execute()
        )

        if len(meters_result.data) == 0:
            self.log.error("No meter found to disable")
            sys.exit(10)

        meters_to_disable = meters_result.data
        self.log.info(f"Processing {len(meters_to_disable)} meters")

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(self.run_job, meter) for meter in meters_to_disable
            ]

        success_count = 0
        for future in concurrent.futures.as_completed(futures):
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

    runner = PrepayEnabledFlipAllJob(esco=esco)
    runner.run()
