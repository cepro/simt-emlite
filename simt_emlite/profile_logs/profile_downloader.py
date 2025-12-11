#!/usr/bin/env python3
"""
Simple Profile Download Script

This script provides a basic implementation of profile log 1 downloading for a single day.
It takes CLI arguments for serial and date, uses Supabase to get meter info,
and downloads profile log 1 data in chunks for one day.

Usage:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21
"""

import datetime
import logging
from typing import Callable, Dict, List
from supabase import Client as SupabaseClient

from emop_frame_protocol.emop_profile_log_1_response import EmopProfileLog1Response
from emop_frame_protocol.emop_profile_log_2_response import EmopProfileLog2Response

# mypy: disable-error-code="import-untyped"
from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.smip.smip_csv import SMIPCSV
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)


class ProfileDownloader:
    def __init__(self, serial: str, date: datetime.date, output_dir: str = "output"):
        self.serial = serial
        self.date = date
        self.output_dir = output_dir

        self.client: EmliteMediatorClient | None = None
        self.supabase: SupabaseClient | None = None

        self._validate_output_directory()

        # Load configuration
        config = load_config()
        self.supabase_url = config["supabase_url"]
        self.supabase_anon_key = config["supabase_anon_key"]
        self.supabase_access_token = config["supabase_access_token"]
        self.fly_region = config["fly_region"]

        # Load meter info
        self._init_supabase()
        self._fetch_meter_info()
        self._fetch_esco_code()

    def _validate_output_directory(self):
        """Validate that the output directory exists and is writable, or can be created"""
        import os

        # Check if the path exists
        if os.path.exists(self.output_dir):
            # If it exists, it must be a directory
            if not os.path.isdir(self.output_dir):
                raise ValueError(
                    f"Output path '{self.output_dir}' exists but is not a directory. Please provide a directory path, not a file path."
                )
        else:
            # If it doesn't exist, try to create it
            try:
                os.makedirs(self.output_dir, exist_ok=True)
                logger.info(f"Created output directory: {self.output_dir}")
            except OSError as e:
                raise ValueError(
                    f"Cannot create output directory '{self.output_dir}': {e}. Please provide a valid directory path."
                )

    def _init_supabase(self):
        """Initialize Supabase client and get meter info"""
        if not all(
            [self.supabase_url, self.supabase_anon_key, self.supabase_access_token]
        ):
            raise Exception(
                "SUPABASE_URL, SUPABASE_ANON_KEY and/or SUPABASE_ACCESS_TOKEN not set"
            )

        self.supabase = supa_client(
            str(self.supabase_url),
            str(self.supabase_anon_key),
            str(self.supabase_access_token),
        )

    def _fetch_meter_info(self):
        result = (
            self.supabase.table("meter_registry")
            .select("id,esco,single_meter_app")
            .eq("serial", self.serial)
            .execute()
        )

        if len(result.data) == 0:
            raise Exception(f"Meter {self.serial} not found in registry")

        meter_data = result.data[0]
        self.meter_id = meter_data["id"]
        self.esco_id = meter_data["esco"]
        self.is_single_meter_app = meter_data["single_meter_app"]

        logger.info(
            f"Found meter [{self.serial}]. id: [{self.meter_id}], is_single_meter_app=[{self.is_single_meter_app}]"
        )

    def _fetch_esco_code(self):
        self.esco_code = None
        if self.esco_id is not None:
            result = (
                self.supabase.schema("flows")
                .table("escos")
                .select("code")
                .eq("id", self.esco_id)
                .execute()
            )
            self.esco_code = result.data[0]["code"] if result.data else None
            logger.info(f"Found esco_code [{self.esco_code}] for esco [{self.esco_id}]")

    def _init_emlite_client(self):
        """Initialize the Emlite mediator client"""
        containers = get_instance(
            is_single_meter_app=self.is_single_meter_app,
            esco=self.esco_code,
            serial=self.serial,
            region=self.fly_region,
        )

        mediator_address = containers.mediator_address(self.meter_id, self.serial)
        if not mediator_address:
            raise Exception("Unable to get mediator address")

        self.client = EmliteMediatorClient(
            mediator_address=mediator_address,
            meter_id=self.meter_id,
            use_cert_auth=self.is_single_meter_app,
            logging_level=logging.INFO,
        )

        logger.info(f"Connected to mediator at {mediator_address}")

    def _download_profile_log_day(
        self,
        log_fn: str
    ) -> Dict[datetime.datetime, object]:
        """Generic function to download profile log data for a single day in chunks

        Args:
            log_fn: Name of the log function on the Emlite client. Used to fetch records but also for logging.

        Returns:
            Dict of timestamp to profile record
        """
        if not self.client:
            self._init_emlite_client()

        # Convert date to datetime for the day (ensure timezone-aware)
        start_datetime = datetime.datetime.combine(
            self.date, datetime.time.min
        ).replace(tzinfo=datetime.timezone.utc)
        end_datetime = datetime.datetime.combine(self.date, datetime.time.max).replace(
            tzinfo=datetime.timezone.utc
        )

        logger.info(f"Downloading {log_fn} data for {self.date}")

        fetch_func: Callable[[datetime.datetime], EmopProfileLog1Response | EmopProfileLog2Response] = getattr(self.client, log_fn)

        # Download in 2-hour chunks (4 x 30-minute intervals per chunk)
        current_time = start_datetime
        chunk_size = datetime.timedelta(hours=2)
        profile_records: Dict[datetime.datetime, object] = {}

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)

            logger.info(f"Downloading chunk: {current_time} to {chunk_end}")

            try:
                # Download profile log for this chunk
                response = fetch_func(current_time)
                if response and response.records:
                    logger.info(
                        f"Received {len(response.records)} records for {current_time}"
                    )
                    # future time out of range - see #382 - meters will return the next
                    # available data even if that is months ahead
                    if response.records[0].timestamp > end_datetime:
                        logger.warning(
                            "Future date returned - skipping remainder for this period"
                        )
                        return profile_records

                    for record in response.records:
                        profile_records[record.timestamp] = record

            except Exception as e:
                logger.error(f"Error downloading chunk {current_time}: {e}")
                break

            # Move to next chunk
            current_time = chunk_end

        logger.info(f"{log_fn} download completed")

        return profile_records

    def download_profile_log_1_day(self) -> Dict[datetime.datetime, object]:
        """Download profile log 1 data for a single day in chunks"""
        return self._download_profile_log_day("profile_log_1")

    def download_profile_log_2_day(self) -> Dict[datetime.datetime, object]:
        """Download profile log 2 data for a single day in chunks"""
        return self._download_profile_log_day("profile_log_2")

    def _write_csv_output(self, records: List[dict]):
        try:
            # Write CSV using our SMIP CSV writer
            SMIPCSV.write_from_profile_records(
                serial=self.serial,
                output_dir=self.output_dir,
                profile_records=records,
                date=self.date,
            )
            logger.info(
                f"Successfully wrote {len(records)} records to CSV file"
            )
        except Exception as e:
            logger.error(f"Failed to write CSV output: {e}", exc_info=True)
            raise
