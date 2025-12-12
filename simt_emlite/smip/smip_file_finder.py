#!/usr/bin/env python3
"""
SMIP File Finder implementation based on Java SMIPFileFinder class

This class provides functionality to find SMIP files in a directory based on various criteria.
"""

from datetime import date
from pathlib import Path
from typing import List, Optional

from .smip_file_finder_result import SMIPFileFinderResult
from .smip_filename import ElementMarker, SMIPFilename


class SMIPFileFinder:
    """
    Represents a Simtricity import/export file finder.

    Encapsulates the filename format including file marker variations indicating
    if a file has been ingested or not.
    """

    @staticmethod
    def find(
        directory: Path, filename_prefix: str, filename_day: date
    ) -> SMIPFileFinderResult:
        """
        Look in a given directory for an SMIP file with a given prefix and day.

        Args:
            directory: Look for the file(s) in this directory
            filename_prefix: SMIPFilename.prefix
            filename_day: SMIPFilename.day

        Returns:
            Results of the find including the File if found.
        """
        return SMIPFileFinder._find_internal(
            directory, filename_prefix, filename_day, None
        )

    @staticmethod
    def find_with_element(
        directory: Path,
        filename_prefix: str,
        filename_day: date,
        element_marker: ElementMarker,
    ) -> SMIPFileFinderResult:
        """
        Look in a given directory for an SMIP file with a given prefix, day and element.

        Args:
            directory: Look for the file(s) in this directory
            filename_prefix: SMIPFilename.prefix
            filename_day: SMIPFilename.day
            element_marker: SMIPFilename.ElementMarker

        Returns:
            Results of the find including the File if found.
        """
        return SMIPFileFinder._find_internal(
            directory, filename_prefix, filename_day, element_marker
        )

    @staticmethod
    def _find_internal(
        directory: Path,
        filename_prefix: str,
        filename_day: date,
        element_marker: Optional[ElementMarker],
    ) -> SMIPFileFinderResult:
        """
        Internal implementation of find logic.

        Args:
            directory: Look for the file(s) in this directory
            filename_prefix: SMIPFilename.prefix
            filename_day: SMIPFilename.day
            element_marker: SMIPFilename.ElementMarker (optional)

        Returns:
            Results of the find including the File if found.
        """
        # Create prefix with day (and element if provided)
        if element_marker is None:
            prefix_with_day = SMIPFilename(
                filename_prefix, filename_day
            ).serial_element_day_prefix()
        else:
            prefix_with_day = SMIPFilename(
                filename_prefix, filename_day, element_marker
            ).serial_element_day_prefix()

        # Find files that start with the prefix
        matching_files = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name.startswith(prefix_with_day):
                matching_files.append(file_path)

        if not matching_files:
            return SMIPFileFinderResult(False, False, None)

        # Get the first matching file
        dl_file = matching_files[0]
        dl_filename = SMIPFilename.from_filename(dl_file.name)

        return SMIPFileFinderResult(
            dl_filename.is_ingested_simtricity(),
            dl_filename.is_ingested_timescale(),
            dl_file,
        )

    @staticmethod
    def find_downloaded(directory: Path) -> List[Path]:
        """
        Look in a given directory for ALL files that have been downloaded but not
        yet ingested. That is, all files whose name matches the standard format
        but don't have any ingestion markers - _s, _t, _st ...

        Args:
            directory: Look for the file(s) in this directory

        Returns:
            List of matching files sorted by filename.
        """
        downloaded_files = []
        for file_path in directory.iterdir():
            if (
                file_path.is_file()
                and SMIPFilename.DOWNLOADED_FILENAME_PATTERN.fullmatch(file_path.name)
            ):
                downloaded_files.append(file_path)

        # Sort files by filename
        downloaded_files.sort(key=lambda x: x.name)
        return downloaded_files
