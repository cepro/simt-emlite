#!/usr/bin/env python3
"""
SMIP File Finder Result implementation based on Java SMIPFileFinderResult class

This class represents the summary of the result of an SMIPFileFinder run.
"""

from typing import Optional
from pathlib import Path

class SMIPFileFinderResult:
    """
    Summary of the result of an SMIPFileFinder run.
    """

    def __init__(self, ingested_simtricity: bool, ingested_timescale: bool, smip_file: Optional[Path]):
        """
        Create an SMIPFileFinderResult instance.

        Args:
            ingested_simtricity: Whether the file has been ingested into Simtricity
            ingested_timescale: Whether the file has been ingested into Timescale
            smip_file: Path to the SMIP file (or None if not found)
        """
        self.ingested_simtricity = ingested_simtricity
        self.ingested_timescale = ingested_timescale
        self.smip_file = smip_file
        self.found = smip_file is not None and smip_file.exists()

    def ingested(self) -> bool:
        """
        Has the file been ingested into any database.

        Returns:
            True if ingested into Simtricity or Timescale, False otherwise
        """
        return self.ingested_simtricity or self.ingested_timescale
