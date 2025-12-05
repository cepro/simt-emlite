#!/usr/bin/env python3
"""
Simple Profile Download Script

This script provides a basic implementation of profile log 1 downloading for a single day.
It takes CLI arguments for serial and date, uses Supabase to get meter info,
and downloads profile log 1 data in chunks for one day.

Usage:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21
"""

import argparse
import datetime
import logging
import sys
import time
from typing import List

# mypy: disable-error-code="import-untyped"
from emop_frame_protocol.emop_profile_log_1_response import EmopProfileLog1Response

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.smip.smip_csv import SMIPCSV, SMIPCSVRecord
from simt_emlite.util.config import load_config
from simt_emlite.util.supabase import supa_client
from simt_emlite.util.timestamp import parse_meter_timestamp, TimestampConversionError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProfileDownloader:
    def __init__(self, serial: str, date: datetime.date, output_dir: str = "output"):
        self.serial = serial
        self.date = date
        self.client = None
        self.supabase = None
        self.output_dir = output_dir
        self.profile_records: List[dict] = []  # Store records for CSV writing

        # Validate that output_dir is a directory or can be created
        self._validate_output_directory()

        # Load configuration
        config = load_config()
        self.supabase_url = config["supabase_url"]
        self.supabase_anon_key = config["supabase_anon_key"]
        self.supabase_access_token = config["supabase_access_token"]
        self.fly_region = config["fly_region"]

        # Initialize Supabase client
        self._init_supabase()

    def _validate_output_directory(self):
        """Validate that the output directory exists and is writable, or can be created"""
        import os

        # Check if the path exists
        if os.path.exists(self.output_dir):
            # If it exists, it must be a directory
            if not os.path.isdir(self.output_dir):
                raise ValueError(f"Output path '{self.output_dir}' exists but is not a directory. Please provide a directory path, not a file path.")
        else:
            # If it doesn't exist, try to create it
            try:
                os.makedirs(self.output_dir, exist_ok=True)
                logger.info(f"Created output directory: {self.output_dir}")
            except OSError as e:
                raise ValueError(f"Cannot create output directory '{self.output_dir}': {e}. Please provide a valid directory path.")

    def _init_supabase(self):
        """Initialize Supabase client and get meter info"""
        if not all([self.supabase_url, self.supabase_anon_key, self.supabase_access_token]):
            raise Exception("Supabase configuration not set")

        self.supabase = supa_client(
            str(self.supabase_url),
            str(self.supabase_anon_key),
            str(self.supabase_access_token)
        )

        # Get meter info from registry
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

        # Get ESCO code if available
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

        logger.info(f"Found meter {self.serial} with ID {self.meter_id}")

    def _init_client(self):
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

    def download_profile_log_1_day(self):
        """Download profile log 1 data for a single day in chunks"""
        if not self.client:
            self._init_client()

        # Convert date to datetime for the day (ensure timezone-aware)
        start_datetime = datetime.datetime.combine(self.date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        end_datetime = datetime.datetime.combine(self.date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)

        logger.info(f"Downloading profile log 1 data for {self.date}")

        # Download in 2-hour chunks (4 x 30-minute intervals per chunk)
        current_time = start_datetime
        chunk_size = datetime.timedelta(hours=2)

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)

            logger.info(f"Downloading chunk: {current_time} to {chunk_end}")

            try:
                # Download profile log 1 for this chunk
                response = self.client.profile_log_1(current_time)
                self._collect_profile_records(response, current_time)

            except Exception as e:
                logger.error(f"Error downloading chunk {current_time}: {e}")
                # Continue with next chunk even if this one fails

            # Move to next chunk
            current_time = chunk_end

            # Small delay between chunks to avoid overwhelming the meter
            time.sleep(1)

        logger.info("Profile log 1 download completed")

        # Write collected records to CSV
        self._write_csv_output()

    def _write_csv_output(self):
        """Write collected profile records to CSV file"""
        if not self.profile_records:
            logger.warning("No profile records to write to CSV")
            return

        try:
            # Write CSV using our SMIP CSV writer
            SMIPCSV.write_from_profile_records(
                serial=self.serial,
                output_dir=self.output_dir,
                profile_records=self.profile_records,
                date=self.date
            )
            logger.info(f"Successfully wrote {len(self.profile_records)} records to CSV file")
        except Exception as e:
            logger.error(f"Failed to write CSV output: {e}", exc_info=True)
            raise

    def _collect_profile_records(self, response: EmopProfileLog1Response, timestamp: datetime.datetime):
        """Collect profile log 1 response data for CSV writing"""
        if not response or not response.records:
            logger.warning(f"No data received for timestamp {timestamp}")
            return

        logger.info(f"Received {len(response.records)} records for {timestamp}")

        for record in response.records:
            # Convert record to dict format for CSV writing
            try:
                # Use timestamp utility to handle various timestamp formats
                timestamp = parse_meter_timestamp(
                    record.timestamp,
                    reference_date=self.date
                )
            except TimestampConversionError as e:
                logger.error(f"Failed to parse timestamp {record.timestamp}: {e}")
                # Use current time as fallback to avoid breaking the entire process
                timestamp = datetime.datetime.now(datetime.timezone.utc)

            record_dict = {
                'timestamp': timestamp,
                'import_a': record.import_a,
                'import_b': record.import_b,
                'status': record.status,
                'export': getattr(record, 'export', None)  # Add export if available
            }
            self.profile_records.append(record_dict)

def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Simple Profile Download Script - Downloads profile log 1 data for a single day"
    )

    parser.add_argument(
        "--serial",
        "-s",
        help="Meter serial number",
        required=True,
        type=str
    )

    parser.add_argument(
        "--date",
        "-d",
        help="Date to download data for (YYYY-MM-DD format)",
        required=True,
        type=valid_date
    )

    parser.add_argument(
        "--verbose",
        "-v",
        help="Enable verbose logging",
        action="store_true"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for CSV files (default: output). Must be a directory path, not a file path.",
        default="output",
        type=str
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        logger.info(f"Starting profile download for serial {args.serial} on date {args.date}")

        downloader = ProfileDownloader(args.serial, args.date, args.output)
        downloader.download_profile_log_1_day()

        logger.info("Profile download completed successfully")

    except Exception as e:
        logger.error(f"Profile download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
