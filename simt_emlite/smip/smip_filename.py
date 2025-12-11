#!/usr/bin/env python3
"""
SMIP Filename implementation based on Java SMIPFilename class

This class handles the filename format for Simtricity import/export files,
including file markers for ingestion and element identification.
"""

import re
from datetime import date
from enum import Enum
from typing import Optional

class ElementMarker(Enum):
    """For twin elements, mark register 1 'A' and register 2 'B' in filenames."""
    A = "A"
    B = "B"

class IngestionMarker(Enum):
    """Ingestion markers indicate which systems the file has already been ingested into."""
    SIMTRICITY = 's'
    TIMESCALE = 't'

class SMIPFilename:
    """
    Represents a Simtricity import/export file.

    Encapsulates the filename format including file markers for:
     - ingestion
     - element
    """

    # Regex Pattern for optional Element marker used for twin elements meters.
    # Marked by '-A' or '-B' after the serial.
    ELEMENT_MARKER_PATTERN = re.compile(
        r"(-(?P<elementMarker>[AB]))?"
    )

    # Regex Pattern for the ISO timestamp part of the filename.
    ISO_TIMESTAMP_PATTERN = re.compile(
        r"-(?P<tsYear>\d{4})(?P<tsMonth>\d{2})(?P<tsDay>\d{2})"
    )

    # Regex Pattern for ALL possible SMIP files.
    FILENAME_PATTERN = re.compile(
        # Meter serial
        r"(?P<serial>[A-Za-z0-9]*)" +
        ELEMENT_MARKER_PATTERN.pattern +
        ISO_TIMESTAMP_PATTERN.pattern +
        # optional ingestion marker(s) prefixed by underscore
        r"(_" +
        r"(?P<ingestionMarker>" +
        IngestionMarker.SIMTRICITY.value + IngestionMarker.TIMESCALE.value + "|" +
        IngestionMarker.SIMTRICITY.value + "|" +
        IngestionMarker.TIMESCALE.value +
        r")?" +
        # Extension
        r")?.csv"
    )

    # Regex Pattern for files that have been downloaded but not yet ingested.
    # ie. filenames without any ingestion markers like '_s'.
    DOWNLOADED_FILENAME_PATTERN = re.compile(
        r"(EML\d*)" +
        ELEMENT_MARKER_PATTERN.pattern +
        ISO_TIMESTAMP_PATTERN.pattern +
        r".csv"
    )

    def __init__(self, prefix: str, day: date, element: Optional[ElementMarker] = None):
        """
        Create an SMIPFilename instance given the component parts

        Args:
            prefix: Filename prefix, usually the Meter serial number
            day: File contains data for this day
            element: ElementMarker (optional)
        """
        self.prefix = prefix
        self.day = day
        self.element = element
        self.ingested_simtricity = False
        self.ingested_timescale = False

    @classmethod
    def from_filename(cls, filename: str) -> 'SMIPFilename':
        """
        Create an SMIPFilename instance given a full filename.

        Use this constructor when you already have a file and want to extract
        parts from the filename.

        Args:
            filename: Filename

        Returns:
            SMIPFilename instance
        """
        matcher = cls.FILENAME_PATTERN.fullmatch(filename)
        if not matcher:
            raise ValueError(f"Invalid SMIP filename format: {filename}")

        prefix = matcher.group("serial")
        day = date(
            int(matcher.group("tsYear")),
            int(matcher.group("tsMonth")),
            int(matcher.group("tsDay"))
        )

        element_marker_str = matcher.group("elementMarker")
        element = None
        if element_marker_str:
            if element_marker_str == ElementMarker.A.value:
                element = ElementMarker.A
            elif element_marker_str == ElementMarker.B.value:
                element = ElementMarker.B

        ingestion_marker_str = matcher.group("ingestionMarker")
        ingested_simtricity = False
        ingested_timescale = False
        if ingestion_marker_str:
            if IngestionMarker.SIMTRICITY.value in ingestion_marker_str:
                ingested_simtricity = True
            if IngestionMarker.TIMESCALE.value in ingestion_marker_str:
                ingested_timescale = True

        instance = cls(prefix, day, element)
        instance.ingested_simtricity = ingested_simtricity
        instance.ingested_timescale = ingested_timescale
        return instance

    def get_prefix(self) -> str:
        """Return the filename prefix"""
        return self.prefix

    def get_day(self) -> date:
        """Return the day this file contains data for"""
        return self.day

    def get_element_marker(self) -> Optional[ElementMarker]:
        """Return the element marker"""
        return self.element

    def is_ingested_simtricity(self) -> bool:
        """Return whether this file has been ingested into Simtricity"""
        return self.ingested_simtricity

    def is_ingested_timescale(self) -> bool:
        """Return whether this file has been ingested into Timescale"""
        return self.ingested_timescale

    def filename(self, ingested_simtricity: bool = False, ingested_timescale: bool = False) -> str:
        """
        Return the filename for this file with ingestion markers added.

        Args:
            ingested_simtricity: Has been ingested into Simtricity
            ingested_timescale: Has been ingested into Timescale

        Returns:
            Filename with ingestion markers.
        """
        filename_parts = [self.serial_element_day_prefix()]

        marker = self._ingestion_markers_string(ingested_simtricity, ingested_timescale)
        if marker:
            filename_parts.append(f"_{marker}")

        filename_parts.append(".csv")

        return "".join(filename_parts)

    def serial_element_day_prefix(self) -> str:
        """
        Return the filename prefix containing the first 3 parts:
         - serial
         - element marker (if exists)
         - day

        Returns:
            Filename prefix
        """
        parts = [self.prefix]

        if self.element:
            parts.append(self.element.value)

        parts.append(self.day.strftime('%Y%m%d'))

        return "-".join(parts)

    def _ingestion_markers_string(self, ingested_simtricity: bool, ingested_timescale: bool) -> str:
        """Generate ingestion markers string"""
        marker = ""
        if ingested_simtricity:
            marker += IngestionMarker.SIMTRICITY.value
        if ingested_timescale:
            marker += IngestionMarker.TIMESCALE.value
        return marker
