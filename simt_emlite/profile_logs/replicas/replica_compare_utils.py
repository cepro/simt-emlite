import datetime
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .replica_missing_file_utils import extract_date_from_filename


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
    files_1 = scan_replica_folder(folder_1, start_date, end_date)
    files_2 = scan_replica_folder(folder_2, start_date, end_date)

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
