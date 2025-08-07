import argparse
import datetime
import logging
import traceback
from typing import cast
from zoneinfo import ZoneInfo

# mypy: disable-error-code="import-untyped"
from emop_frame_protocol.emop_data import EmopData

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.mediator.mediator_client_exception import (
    MediatorClientException,
)
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)


class ProfileLogFetchJob:
    def __init__(
        self,
        *,
        serial: str,
        day: str,
    ):
        self.serial = serial
        self.day = day

        config = load_config()

        SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
        SUPABASE_ANON_KEY = config["supabase_anon_key"]
        SUPABASE_URL = config["supabase_url"]
        FLY_REGION: str | None = cast(str | None, config["fly_region"])

        if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_ACCESS_TOKEN:
            raise Exception(
                "SUPABASE_URL, SUPABASE_ANON_KEY and/or SUPABASE_ACCESS_TOKEN not set"
            )

        self.supabase = supa_client(
            str(SUPABASE_URL), str(SUPABASE_ANON_KEY), str(SUPABASE_ACCESS_TOKEN)
        )

        # Look up meter details by serial
        result = (
            self.supabase.table("meter_registry")
            .select("id,esco,single_meter_app")
            .eq("serial", serial)
            .execute()
        )
        if len(result.data) == 0:
            raise Exception(f"meter {serial} not found")

        meter = result.data[0]
        meter_id = meter["id"]
        esco_id = meter["esco"]
        is_single_meter_app = meter["single_meter_app"]

        esco_code = None
        if esco_id is not None:
            result = (
                self.supabase.schema("flows")
                .table("escos")
                .select("code")
                .eq("id", esco_id)
                .execute()
            )
            esco_code = result.data[0]["code"]

        containers = get_instance(
            is_single_meter_app=is_single_meter_app,
            esco=esco_code,
            serial=serial,
            region=FLY_REGION,
        )
        mediator_address = containers.mediator_address(meter_id, serial)
        if not mediator_address:
            raise Exception("unable to get mediator address")

        self.emlite_client = EmliteMediatorClient(
            mediator_address=mediator_address,
            meter_id=meter_id,
            use_cert_auth=is_single_meter_app,
            logging_level=logging.INFO,
        )

        global logger
        self.log = logger.bind(
            serial=serial, day=day, meter_id=meter_id, mediator_address=mediator_address
        )

    def fetch_and_print(self):
        try:
            # Parse the day string to timezone-aware datetime
            timestamp = datetime.datetime.strptime(self.day, "%Y-%m-%d").replace(
                tzinfo=ZoneInfo("UTC")
            )

            self.log.info("Fetching profile_log_2", timestamp=timestamp)
            response = self.emlite_client.profile_log_2(timestamp)

            # Print the response to stdout
            print(str(response))

            self.log.info("Successfully fetched and printed profile_log_2")

        except MediatorClientException as e:
            self.log.error(
                "Mediator client failure",
                error=e,
                exception=traceback.format_exception(e),
            )
            raise
        except ValueError as e:
            self.log.error(
                "Invalid date format",
                error=e,
                day=self.day,
            )
            raise
        except Exception as e:
            self.log.error(
                "Unknown failure during profile_log_2 fetch",
                error=e,
                exception=traceback.format_exception(e),
            )
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch profile_log_2 for a single day and print to stdout"
    )
    parser.add_argument(
        "--day",
        required=True,
        action="store",
        help="Day to fetch profile_log_2 for (format: YYYY-MM-DD, e.g., 2025-08-01)",
    )
    parser.add_argument(
        "--serial",
        required=True,
        action="store",
        help="Meter serial number to fetch profile_log_2 for",
    )

    args = parser.parse_args()

    job = ProfileLogFetchJob(
        serial=args.serial,
        day=args.day,
    )

    job.fetch_and_print()
