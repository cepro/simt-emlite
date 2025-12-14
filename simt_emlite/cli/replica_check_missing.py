#!/usr/bin/env python3
"""
Replica Missing Files Checker Script

This script scans a directory structure for missing daily files within a specified date range.
It expects a structure like:
    Root
    |-- Plot-01.C
    |   |-- EML...-A-20251101.csv
    |   |-- ...

Usage:
    python -m simt_emlite.cli.replica_check_missing <root_dir> <start_date> <end_date>
"""

import argparse
import datetime
import sys
from pathlib import Path
from typing import Dict, List

from simt_emlite.profile_logs.replica_utils import check_missing_files


def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def check_missing_files_with_validation(
    root_path: Path,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Dict[str, List[datetime.date]]:
    """Wrapper around check_missing_files that validates root path exists."""
    if not root_path.exists():
        print(f"Error: Root folder does not exist: {root_path}")
        sys.exit(2)

    return check_missing_files(root_path, start_date, end_date)


def print_report(
    missing_map: Dict[str, List[datetime.date]],
    start_date: datetime.date,
    end_date: datetime.date,
) -> None:
    """Print the missing files report."""
    print("\n" + "=" * 80)
    print("MISSING FILES REPORT")
    print("=" * 80)
    print(f"Date Range: {start_date} to {end_date}")

    if not missing_map:
        print("\nSUCCESS: No missing files found in the scanned directories.")
        return

    print(f"\nFound missing files in {len(missing_map)} directories:")

    for dir_path, dates in sorted(missing_map.items()):
        print(f"\nDirectory: {dir_path}")
        print(f"  Missing {len(dates)} day(s):")

        # Group consecutive dates for cleaner output
        if not dates:
            continue

        ranges: List[str] = []
        if len(dates) == 1:
            ranges.append(str(dates[0]))
        else:
            range_start = dates[0]
            prev = dates[0]

            for current in dates[1:]:
                if (current - prev).days > 1:
                    # Gap found, close previous range
                    if range_start == prev:
                        ranges.append(f"{range_start}")
                    else:
                        ranges.append(f"{range_start} to {prev}")
                    range_start = current
                prev = current

            # Close final range
            if range_start == prev:
                ranges.append(f"{range_start}")
            else:
                ranges.append(f"{range_start} to {prev}")

        for r in ranges:
            print(f"    - {r}")


def main():
    parser = argparse.ArgumentParser(
        description="Check for missing daily files in a directory structure."
    )

    parser.add_argument(
        "root_folder",
        help="Root folder to scan (containing Plot-XX subfolders)",
        type=Path,
    )

    parser.add_argument(
        "start_date",
        help="Start date (YYYY-MM-DD)",
        type=valid_date,
    )

    parser.add_argument(
        "end_date",
        help="End date (YYYY-MM-DD)",
        type=valid_date,
    )

    args = parser.parse_args()

    missing_map = check_missing_files_with_validation(
        args.root_folder, args.start_date, args.end_date
    )
    print_report(missing_map, args.start_date, args.end_date)

    if missing_map:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
