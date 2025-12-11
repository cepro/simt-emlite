import argparse
import concurrent.futures
import os
import sys
import traceback
from decimal import Decimal

import requests

from simt_emlite.jobs.future_tariffs_update import FutureTariffsUpdateJob
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
public_backend_role_key: str | None = os.environ.get("PUBLIC_BACKEND_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)
env: str | None = os.environ.get("ENV")


"""
    Update future tariffs for all meters that require it.
"""


class FutureTariffsUpdateAllJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        self.esco = esco
        self.containers = get_instance(esco=esco, env=env)
        self.flows_supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.backend_supabase = supa_client(
            supabase_url, supabase_key, public_backend_role_key, schema="myenergy"
        )

        # {
        #     "serial": "EML2244826972",
        #     "meter_id": "b1b8ccaf-930f-4e35-a016-95d677ded96b",
        #     "customer_id": "2bf6e3d4-d41d-4982-9b7a-6957a4f549bc",
        #     "customer_email": "plot11-qa@waterlilies.energy",
        #     "esco_code": "lab",
        #     "tariff_period_start": "2025-04-01",
        #     "customer_unit_rate": 0.17782,
        #     "customer_standing_charge": 0.51082,
        #     "emergency_credit": null,
        #     "debt_recovery_rate": null,
        #     "ecredit_button_threshold": null,
        #     "current_future_standing_charge": null,
        #     "current_future_unit_rate_a": null,
        #     "current_future_unit_rate_b": null,
        #     "current_future_activation_datetime": null
        # }

    def run_job(self, tariff):
        meter_id = tariff["meter_id"]
        serial = tariff["serial"]

        # look up meter in the flows meter_registry checking it's active
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
            return False

        meter_id = meter_query.data[0]["id"]

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

            job = FutureTariffsUpdateJob(
                tariff=tariff,
                mediator_address=mediator_address,
                supabase=self.backend_supabase,
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
        self.log.info("Starting future tariffs update all job...")

        tariffs = self.future_tariffs_to_update(self.esco)
        self.log.info(f"response JSON [{tariffs}]")

        if len(tariffs) == 0:
            self.log.info("No tariffs to update for " + self.esco)
            sys.exit(10)

        self.log.info(f"Processing {len(tariffs)} future tariff updates")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_parallel_jobs
        ) as executor:
            futures = [executor.submit(self.run_job, tariff) for tariff in tariffs]

        results = concurrent.futures.wait(futures)

        success_count = sum(1 for future in results.done if future.result())

        self.log.info(
            f"Finished tariffs update all job. Success: {success_count}/{len(tariffs)}"
        )

    def future_tariffs_to_update(self, esco: str):
        return self._call_rpc(
            "meters_missing_future_tariffs",
            data={"esco_code_in": esco},
        )

    def _call_rpc(self, name: str, data: dict | None = None):
        api_base_uri = f"{supabase_url}/rest/v1"

        api_headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {public_backend_role_key}",
            "Accept-Profile": "public",
        }

        response = requests.post(
            url=f"{api_base_uri}/rpc/{name}", headers=api_headers, data=data
        )
        self.log.info(f"{name} response [{response}]")

        return self._convert_floats_to_decimal(response.json())

    def _convert_floats_to_decimal(self, data_list):
        return [
            {
                k: (Decimal(str(v)) if isinstance(v, float) else v)
                for k, v in item.items()
            }
            for item in data_list
        ]

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
        help="Apply tariff updates to meters in this ESCO only",
    )
    args = parser.parse_args()

    esco = args.esco if hasattr(args, "esco") else None

    runner = FutureTariffsUpdateAllJob(esco=esco)
    runner.run()
