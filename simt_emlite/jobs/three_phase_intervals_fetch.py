import argparse
import datetime
import logging
import os
import traceback
from typing import cast
from zoneinfo import ZoneInfo

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.mediator.mediator_client_exception import (
    MediatorClientException,
)
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

logger = get_logger(__name__, __file__)


class ThreePhaseIntervalsFetchJob:
    def __init__(
        self,
        *,
        serial: str,
        folder: str,
        start_day: str | None = None,
        end_day: str | None = None,
        day: str | None = None,
        include_statuses: bool = False,
    ):
        self.serial = serial
        self.folder = folder
        self.start_day = start_day
        self.end_day = end_day
        self.day = day
        self.include_statuses = include_statuses

        # Ensure folder exists
        os.makedirs(folder, exist_ok=True)

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
            .select("id,esco")
            .eq("serial", serial)
            .execute()
        )
        if len(as_list(result)) == 0:
            raise Exception(f"meter {serial} not found")

        meter = as_first_item(result)
        meter_id = meter["id"]
        esco_id = meter["esco"]

        esco_code = None
        if esco_id is not None:
            result = (
                self.supabase.schema("flows")
                .table("escos")
                .select("code")
                .eq("id", esco_id)
                .execute()
            )
            esco_code = as_first_item(result)["code"]

        containers = get_instance(
            is_single_meter_app=False,
            esco=esco_code,
            serial=serial,
            region=FLY_REGION,
        )
        mediator_address = containers.mediator_address(meter_id, serial)
        if not mediator_address:
            raise Exception("unable to get mediator address")

        self.emlite_client = EmliteMediatorClient(
            mediator_address=mediator_address,
            logging_level=logging.INFO,
        )

        global logger
        self.log = logger.bind(
            serial=serial, meter_id=meter_id, mediator_address=mediator_address
        )

    def _generate_csv_filename(self, day: str) -> str:
        """Generate CSV filename with serial and day"""
        return os.path.join(self.folder, f"{self.serial}_{day}_intervals.csv")

    def _parse_day(self, day_str: str) -> datetime.datetime:
        """Parse day string to timezone-aware datetime"""
        return datetime.datetime.strptime(day_str, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("UTC")
        )

    def _generate_date_range(self) -> list[str]:
        """Generate list of date strings from start_day to end_day (inclusive)"""
        if self.day:
            return [self.day]

        if not self.start_day or not self.end_day:
            raise ValueError("Either --day or both --start-day and --end-day must be provided")

        start_date = datetime.datetime.strptime(self.start_day, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(self.end_day, "%Y-%m-%d").date()

        if start_date > end_date:
            raise ValueError("start_day must be before or equal to end_day")

        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += datetime.timedelta(days=1)

        return dates

    def fetch_intervals(self):
        try:
            dates = self._generate_date_range()

            for day_str in dates:
                day_dt = self._parse_day(day_str)
                csv_filename = self._generate_csv_filename(day_str)

                self.log.info("Fetching three_phase_intervals", day=day_str, csv_file=csv_filename)

                # Call three_phase_intervals with day parameter (start_time and end_time will be ignored)
                intervals = self.emlite_client.three_phase_intervals(
                    self.serial,
                    day=day_dt,
                    start_time=None,  # Will be ignored when day is provided
                    end_time=None,    # Will be ignored when day is provided
                    csv=csv_filename,
                    include_statuses=self.include_statuses,
                )

                self.log.info("Successfully fetched three_phase_intervals",
                             day=day_str,
                             csv_file=csv_filename,
                             interval_count=len(intervals.intervals))

        except MediatorClientException as e:
            self.log.error(
                "Mediator client failure",
                error=e,
                exception=traceback.format_exception(e),
            )
            raise
        except ValueError as e:
            self.log.error(
                "Invalid date format or range",
                error=e,
            )
            raise
        except Exception as e:
            self.log.error(
                "Unknown failure during three_phase_intervals fetch",
                error=e,
                exception=traceback.format_exception(e),
            )
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch three_phase_intervals for day(s) and save as CSV files"
    )

    # Serial and folder are required
    parser.add_argument(
        "--serial",
        required=True,
        action="store",
        help="Meter serial number to fetch intervals for",
    )
    parser.add_argument(
        "--folder",
        required=True,
        action="store",
        help="Folder to save CSV files in",
    )

    # Date options - either single day or range
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--day",
        action="store",
        help="Single day to fetch intervals for (format: YYYY-MM-DD, e.g., 2025-08-01)",
    )
    date_group.add_argument(
        "--start-day",
        action="store",
        help="Start day for date range (format: YYYY-MM-DD, e.g., 2025-08-01). Must be used with --end-day",
    )

    # End day only valid with start day
    parser.add_argument(
        "--end-day",
        action="store",
        help="End day for date range (format: YYYY-MM-DD, e.g., 2025-08-05). Must be used with --start-day",
    )

    # Optional flag for including statuses
    parser.add_argument(
        "--include-statuses",
        action="store_true",
        help="Include status information in CSV output",
    )

    args = parser.parse_args()

    # Validate that start-day and end-day are used together
    if (args.start_day and not args.end_day) or (args.end_day and not args.start_day):
        parser.error("--start-day and --end-day must be used together")

    job = ThreePhaseIntervalsFetchJob(
        serial=args.serial,
        folder=args.folder,
        start_day=args.start_day,
        end_day=args.end_day,
        day=args.day,
        include_statuses=args.include_statuses,
    )

    job.fetch_intervals()
