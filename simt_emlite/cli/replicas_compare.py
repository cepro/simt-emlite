#!/usr/bin/env python3
"""
Replica Folder Comparator Script

This script compares two replica folders containing CSV files with dated filenames.
Files are filtered by an optional date range extracted from the filename pattern:
    EML2137580797-A-20210915.csv (where 20210915 is the date YYYYMMDD)

Usage:
    python -m simt_emlite.cli.replicas_compare <replica_dir_1> <replica_dir_2> [start_date] [end_date]

Output Report Sections:
    1. Files in folder 1 but not in folder 2
    2. Files in folder 2 but not in folder 1
    3. Files in both but different (with size difference)
"""

import argparse
import datetime
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Regex pattern to extract date from filename (e.g., EML2137580797-A-20210915.csv)
DATE_PATTERN = re.compile(r".*-(\d{8})\.csv$")

USAGE_EXAMPLES = """
Examples:
  Compare all files in two replicas:
    python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2

  Compare files within a date range:
    python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2 2021-09-01 2021-09-30
"""


@dataclass
class FileInfo:
    """Information about a file for comparison."""

    relative_path: str
    absolute_path: str
    size: int
    date: Optional[datetime.date]


@dataclass
class FileDifference:
    """Represents a difference between two files."""

    relative_path: str
    size_1: int
    size_2: int
    size_diff: int


@dataclass
class ComparisonReport:
    """Report containing comparison results."""

    only_in_folder_1: List[FileInfo]
    only_in_folder_2: List[FileInfo]
    different_files: List[FileDifference]
    identical_files: int
    total_files_1: int
    total_files_2: int


def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def extract_date_from_filename(filename: str) -> Optional[datetime.date]:
    """Extract date from filename pattern like EML2137580797-A-20210915.csv.

    Args:
        filename: The filename to extract date from

    Returns:
        The extracted date, or None if pattern doesn't match
    """
    match = DATE_PATTERN.match(filename)
    if match:
        date_str = match.group(1)
        try:
            return datetime.datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            return None
    return None


def is_within_date_range(
    file_date: Optional[datetime.date],
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
) -> bool:
    """Check if a file date is within the specified date range.

    Args:
        file_date: The date extracted from the filename
        start_date: Start of date range (inclusive), None means no lower bound
        end_date: End of date range (inclusive), None means no upper bound

    Returns:
        True if within range or no date range specified
    """
    # If no date range is specified, include all files
    if start_date is None and end_date is None:
        return True

    # If file has no date, exclude it when date range is specified
    if file_date is None:
        return False

    if start_date is not None and file_date < start_date:
        return False
    if end_date is not None and file_date > end_date:
        return False

    return True


def scan_replica_folder(
    base_path: Path,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> Dict[str, FileInfo]:
    """Scan a replica folder and build a map of relative paths to FileInfo.

    Args:
        base_path: The root path of the replica folder
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        Dictionary mapping relative path to FileInfo
    """
    file_map: Dict[str, FileInfo] = {}

    if not base_path.exists():
        print(f"Warning: Folder does not exist: {base_path}")
        return file_map

    for root, _dirs, files in os.walk(base_path):
        for filename in files:
            if not filename.endswith(".csv"):
                continue

            absolute_path = Path(root) / filename
            relative_path = str(absolute_path.relative_to(base_path))

            file_date = extract_date_from_filename(filename)

            # Filter by date range
            if not is_within_date_range(file_date, start_date, end_date):
                continue

            try:
                size = absolute_path.stat().st_size
            except OSError:
                size = 0

            file_map[relative_path] = FileInfo(
                relative_path=relative_path,
                absolute_path=str(absolute_path),
                size=size,
                date=file_date,
            )

    return file_map


def compare_replicas(
    folder_1: Path,
    folder_2: Path,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> ComparisonReport:
    """Compare two replica folders and generate a comparison report.

    Args:
        folder_1: Path to the first replica folder
        folder_2: Path to the second replica folder
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering

    Returns:
        ComparisonReport with the results
    """
    print(f"Scanning folder 1: {folder_1}")
    files_1 = scan_replica_folder(folder_1, start_date, end_date)
    print(f"  Found {len(files_1)} CSV files")

    print(f"Scanning folder 2: {folder_2}")
    files_2 = scan_replica_folder(folder_2, start_date, end_date)
    print(f"  Found {len(files_2)} CSV files")

    keys_1: Set[str] = set(files_1.keys())
    keys_2: Set[str] = set(files_2.keys())

    # Files only in folder 1
    only_in_1_keys = keys_1 - keys_2
    only_in_folder_1 = [files_1[k] for k in sorted(only_in_1_keys)]

    # Files only in folder 2
    only_in_2_keys = keys_2 - keys_1
    only_in_folder_2 = [files_2[k] for k in sorted(only_in_2_keys)]

    # Files in both - check for differences
    common_keys = keys_1 & keys_2
    different_files: List[FileDifference] = []
    identical_count = 0

    for key in sorted(common_keys):
        file_1 = files_1[key]
        file_2 = files_2[key]

        if file_1.size != file_2.size:
            different_files.append(
                FileDifference(
                    relative_path=key,
                    size_1=file_1.size,
                    size_2=file_2.size,
                    size_diff=file_2.size - file_1.size,
                )
            )
        else:
            identical_count += 1

    return ComparisonReport(
        only_in_folder_1=only_in_folder_1,
        only_in_folder_2=only_in_folder_2,
        different_files=different_files,
        identical_files=identical_count,
        total_files_1=len(files_1),
        total_files_2=len(files_2),
    )


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if abs(size_bytes) < 1024:
        return f"{size_bytes} B"
    elif abs(size_bytes) < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_size_diff(size_diff: int) -> str:
    """Format size difference with +/- prefix."""
    prefix = "+" if size_diff > 0 else ""
    return f"{prefix}{format_size(size_diff)}"


def print_report(
    report: ComparisonReport,
    folder_1: Path,
    folder_2: Path,
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
) -> None:
    """Print the comparison report to stdout.

    Args:
        report: The comparison report to print
        folder_1: Path to folder 1 (for display)
        folder_2: Path to folder 2 (for display)
        start_date: Start date filter (for display)
        end_date: End date filter (for display)
    """
    print("\n" + "=" * 80)
    print("REPLICA COMPARISON REPORT")
    print("=" * 80)

    print(f"\nFolder 1: {folder_1}")
    print(f"Folder 2: {folder_2}")

    if start_date or end_date:
        date_range = f"{start_date or 'any'} to {end_date or 'any'}"
        print(f"Date Range: {date_range}")

    print(f"\nTotal files in Folder 1: {report.total_files_1}")
    print(f"Total files in Folder 2: {report.total_files_2}")
    print(f"Identical files: {report.identical_files}")

    # Section 1: Files only in folder 1
    print("\n" + "-" * 80)
    print(f"SECTION 1: Files only in Folder 1 ({len(report.only_in_folder_1)} files)")
    print("-" * 80)

    if report.only_in_folder_1:
        for file_info in report.only_in_folder_1:
            print(f"  {file_info.relative_path} ({format_size(file_info.size)})")
    else:
        print("  (none)")

    # Section 2: Files only in folder 2
    print("\n" + "-" * 80)
    print(f"SECTION 2: Files only in Folder 2 ({len(report.only_in_folder_2)} files)")
    print("-" * 80)

    if report.only_in_folder_2:
        for file_info in report.only_in_folder_2:
            print(f"  {file_info.relative_path} ({format_size(file_info.size)})")
    else:
        print("  (none)")

    # Section 3: Different files
    print("\n" + "-" * 80)
    print(f"SECTION 3: Files with differences ({len(report.different_files)} files)")
    print("-" * 80)

    if report.different_files:
        print(f"  {'File':<50} {'Size 1':<12} {'Size 2':<12} {'Diff':<12}")
        print(f"  {'-' * 50} {'-' * 12} {'-' * 12} {'-' * 12}")

        for diff in report.different_files:
            # Truncate filename if too long
            display_path = diff.relative_path
            if len(display_path) > 48:
                display_path = "..." + display_path[-45:]

            print(
                f"  {display_path:<50} "
                f"{format_size(diff.size_1):<12} "
                f"{format_size(diff.size_2):<12} "
                f"{format_size_diff(diff.size_diff):<12}"
            )
    else:
        print("  (none)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_differences = (
        len(report.only_in_folder_1)
        + len(report.only_in_folder_2)
        + len(report.different_files)
    )

    if total_differences == 0:
        print("  ✓ Folders are identical!")
    else:
        print(f"  ✗ Found {total_differences} difference(s):")
        if report.only_in_folder_1:
            print(f"    - {len(report.only_in_folder_1)} file(s) only in Folder 1")
        if report.only_in_folder_2:
            print(f"    - {len(report.only_in_folder_2)} file(s) only in Folder 2")
        if report.different_files:
            print(f"    - {len(report.different_files)} file(s) with size differences")

    print()


def main() -> Tuple[int, ComparisonReport | None]:
    """Main entry point for the replica comparator script.

    Returns:
        Tuple of (exit_code, report) where exit_code is:
        - 0 if folders are identical
        - 1 if there are differences
        - 2 if there was an error
    """
    parser = argparse.ArgumentParser(
        description="Compare two replica folders containing dated CSV files",
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "folder_1",
        help="Path to the first replica folder",
        type=Path,
    )

    parser.add_argument(
        "folder_2",
        help="Path to the second replica folder",
        type=Path,
    )

    parser.add_argument(
        "start_date",
        nargs="?",
        help="Start date for filtering (YYYY-MM-DD format, optional)",
        type=valid_date,
        default=None,
    )

    parser.add_argument(
        "end_date",
        nargs="?",
        help="End date for filtering (YYYY-MM-DD format, optional)",
        type=valid_date,
        default=None,
    )

    args = parser.parse_args()

    # Validate folders exist
    if not args.folder_1.exists():
        print(f"Error: Folder 1 does not exist: {args.folder_1}")
        return 2, None

    if not args.folder_2.exists():
        print(f"Error: Folder 2 does not exist: {args.folder_2}")
        return 2, None

    try:
        report = compare_replicas(
            folder_1=args.folder_1,
            folder_2=args.folder_2,
            start_date=args.start_date,
            end_date=args.end_date,
        )

        print_report(
            report=report,
            folder_1=args.folder_1,
            folder_2=args.folder_2,
            start_date=args.start_date,
            end_date=args.end_date,
        )

        # Return exit code based on whether there are differences
        total_differences = (
            len(report.only_in_folder_1)
            + len(report.only_in_folder_2)
            + len(report.different_files)
        )

        return (0 if total_differences == 0 else 1), report

    except Exception as e:
        print(f"Error during comparison: {e}")
        import traceback

        traceback.print_exc()
        return 2, None


if __name__ == "__main__":
    exit_code, _report = main()
    sys.exit(exit_code)
