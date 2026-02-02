import argparse
import concurrent.futures
import os
import sys
import traceback
from decimal import Decimal


from simt_emlite.jobs.future_tariffs_update import FutureTariffsUpdateJob
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
public_backend_role_key: str | None = os.environ.get("PUBLIC_BACKEND_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)
mediator_server: str | None = os.environ.get("MEDIATOR_SERVER")


"""
    Update future tariffs for all meters that require it.
"""


class FutureTariffsUpdateAllJob:
    def __init__(self, esco=None):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        # Narrow types after environment check
        assert supabase_url is not None
        assert supabase_key is not None

        self.esco = esco
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

        if len(as_list(meter_query)) == 0:
            self.log.error(
                f"No active meter found in meter_registry with serial {serial}"
            )
            return False

        meter_id = as_first_item(meter_query)["id"]

        mediator_address = str(mediator_server)

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
        result = self.backend_supabase.rpc(
            "meters_missing_future_tariffs",
            {"esco_code_in": esco},
        ).execute()

        self.log.info(f"meters_missing_future_tariffs response [{result}]")

        json_data = result.data

        # Handle case where response is not a list (e.g., error message or null)
        if not isinstance(json_data, list):
            self.log.warning(
                "RPC call 'meters_missing_future_tariffs' returned unexpected data type",
                data_type=type(json_data).__name__,
                data=json_data,
            )
            return []

        return self._convert_floats_to_decimal(json_data)

    def _convert_floats_to_decimal(self, data_list: list):
        result = []
        for item in data_list:
            if isinstance(item, dict):
                result.append({
                    k: (Decimal(str(v)) if isinstance(v, float) else v)
                    for k, v in item.items()
                })
            else:
                # If item is not a dict, include it as-is (shouldn't happen normally)
                result.append(item)
        return result

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

        if not mediator_server:
            self.log.error("Environment variable MEDIATOR_SERVER not set.")
            sys.exit(5)


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
