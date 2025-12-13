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
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Regex pattern to extract date from filename (e.g., EML2137580797-A-20210915.csv)
DATE_PATTERN = re.compile(r".*-(\d{8})\.csv$")


def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def extract_date_from_filename(filename: str) -> Optional[datetime.date]:
    """Extract date from filename pattern like EML2137580797-A-20210915.csv."""
    match = DATE_PATTERN.match(filename)
    if match:
        date_str = match.group(1)
        try:
            return datetime.datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            return None
    return None


def generate_date_range(
    start_date: datetime.date, end_date: datetime.date
) -> List[datetime.date]:
    """Generate a list of dates from start to end (inclusive)."""
    delta = end_date - start_date
    return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]


def check_missing_files(
    root_path: Path,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Dict[str, List[datetime.date]]:
    """Scan for missing files in directories containing CSVs.

    Returns:
        Dict mapping directory path (relative to root) to list of missing dates.
    """
    missing_files_map: Dict[str, List[datetime.date]] = {}
    expected_dates = set(generate_date_range(start_date, end_date))

    if not root_path.exists():
        print(f"Error: Root folder does not exist: {root_path}")
        sys.exit(2)

    for dirpath, _, filenames in os.walk(root_path):
        # We only care about this directory if it contains at least one dated CSV file
        # or if it looks like a Plot directory (but might be empty)
        # For now, let's rely on finding at least one relevant file or being a leaf.
        # But if a folder is completely empty, we might miss it.
        # However, checking every folder might be noisy.
        # Let's look for known pattern files.

        found_dates: Set[datetime.date] = set()
        has_csv_files = False

        for filename in filenames:
            d = extract_date_from_filename(filename)
            if d:
                found_dates.add(d)
                has_csv_files = True

        # Heuristic: If we found dated CSV files, we assume this folder represents a time series.
        # If a folder has NO dated CSV files, it might be a parent folder or completely empty.
        # If the user says "Plot-01", "Plot-02", etc., and one is EMPTY, we'd miss it with this heuristic.
        # But if it has *some* files, we check for gaps.
        # The user's request emphasized "missing files for the 5th and 6th", implying gaps.

        if has_csv_files:
            # Check for missing dates
            missing_dates = []
            for d in sorted(list(expected_dates)):
                if d not in found_dates:
                    missing_dates.append(d)

            if missing_dates:
                rel_path = str(Path(dirpath).relative_to(root_path))
                missing_files_map[rel_path] = missing_dates

    return missing_files_map


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

    missing_map = check_missing_files(args.root_folder, args.start_date, args.end_date)
    print_report(missing_map, args.start_date, args.end_date)

    if missing_map:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
