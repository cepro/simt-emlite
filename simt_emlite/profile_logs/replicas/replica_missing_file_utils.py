"""
Replica Utilities Module

Provides utility functions for checking missing files in replica directories.
"""

import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

# Regex pattern to extract date from filename (e.g., EML2137580797-A-20210915.csv)
DATE_PATTERN = re.compile(r".*-(\d{8})\.csv$")


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


def _generate_date_range(
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

    Args:
        root_path: Root path to scan for directories containing CSV files.
        start_date: Start of the date range to check (inclusive).
        end_date: End of the date range to check (inclusive).

    Returns:
        Dict mapping directory path (relative to root) to list of missing dates.
    """
    missing_files_map: Dict[str, List[datetime.date]] = {}
    expected_dates = set(_generate_date_range(start_date, end_date))

    if not root_path.exists():
        return missing_files_map

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


def check_missing_files_for_folder(
    folder_path: Path,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[datetime.date]:
    """Check for missing files in a single folder (not recursive).

    This is useful when you know the exact folder to check, rather than
    scanning a directory tree.

    Args:
        folder_path: Path to the folder containing CSV files.
        start_date: Start of the date range to check (inclusive).
        end_date: End of the date range to check (inclusive).

    Returns:
        Sorted list of missing dates within the specified range.
    """
    expected_dates = set(_generate_date_range(start_date, end_date))

    if not folder_path.exists():
        # If folder doesn't exist, all dates are missing
        return sorted(list(expected_dates))

    found_dates: Set[datetime.date] = set()

    for filename in os.listdir(folder_path):
        d = extract_date_from_filename(filename)
        if d and d in expected_dates:
            found_dates.add(d)

    missing_dates = expected_dates - found_dates
    return sorted(list(missing_dates))
