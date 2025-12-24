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
import sys
from pathlib import Path
from typing import Optional, Tuple

from simt_emlite.profile_logs.replicas.replica_compare_utils import (
    ComparisonReport,
    compare_replicas,
)


def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


USAGE_EXAMPLES = """
Examples:
  Compare all files in two replicas:
    python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2

  Compare files within a date range:
    python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2 2021-09-01 2021-09-30
"""


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
    try:
        exit_code, _report = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: Operation cancelled by user.")
        sys.exit(1)
