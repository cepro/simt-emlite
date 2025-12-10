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

# mypy: disable-error-code="import-untyped"

from simt_emlite.profile_logs.profile_downloader import ProfileDownloader

def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

def main():
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
        downloader.download_profile_log_1_day()

        print("Profile download completed successfully")

    except Exception as e:
        print(f"Profile download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
