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
import sys
import traceback

from typing import Dict

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record

# mypy: disable-error-code="import-untyped"
from simt_emlite.profile_logs.profile_downloader import ProfileDownloader
from simt_emlite.smip.smip_csv import SMIPCSV
from simt_emlite.smip.smip_reading_factory import create_smip_readings



def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile Download Script - Downloads profile log 1 data for a single day"
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
        "--output",
        "-o",
        help="Output directory for CSV files (default: output). Must be a directory path, not a file path.",
        default="output",
        type=str
    )

    args = parser.parse_args()

    try:
        print(f"Starting profile download for serial {args.serial} on date {args.date}")

        downloader = ProfileDownloader(args.serial, args.date, args.output)
        log_1_records: Dict[datetime.datetime, EmopProfileLog1Record] = downloader.download_profile_log_1_day()
        log_2_records: Dict[datetime.datetime, EmopProfileLog2Record]= downloader.download_profile_log_2_day()

        # Create start and end datetime for the day (timezone-aware)
        start_time = datetime.datetime.combine(
            args.date, datetime.time.min
        ).replace(tzinfo=datetime.timezone.utc)
        end_time = datetime.datetime.combine(
            args.date, datetime.time.max
        ).replace(tzinfo=datetime.timezone.utc)

        # Create SMIP readings from the downloaded profile logs
        readings_a, readings_b = create_smip_readings(
            serial=args.serial,
            start_time=start_time,
            end_time=end_time,
            log1_records=log_1_records,
            log2_records=log_2_records,
            is_twin_element=False,  # TODO: Get this from meter info
        )

        print(f"Created {len(readings_a)} SMIP readings for element A")

        # Write readings to CSV
        if readings_a:
            SMIPCSV.write_from_smip_readings(
                serial=args.serial,
                output_dir=args.output,
                readings=readings_a,
                element_marker="A",
            )
            print(f"Wrote {len(readings_a)} readings to CSV in {args.output}")

        if readings_b:
            SMIPCSV.write_from_smip_readings(
                serial=args.serial,
                output_dir=args.output,
                readings=readings_b,
                element_marker="B",
            )
            print(f"Wrote {len(readings_b)} readings to CSV in {args.output}")

        print("Profile download completed successfully")

    except Exception as e:
        print(f"Profile download failed: {e}, exception [{traceback.format_exception(e)}]")
        sys.exit(1)


if __name__ == "__main__":
    main()
