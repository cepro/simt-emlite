#!/usr/bin/env python3
"""
SMIPCSV implementation based on Java SMIPCSV class

This class handles writing profile log data to CSV files in the SMIP format.
"""

import csv
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from .smip_filename import SMIPFilename, ElementMarker

@dataclass
class SMIPCSVRecord:
    """Represents a single record in the SMIP CSV format"""
    timestamp: datetime
    import_value: Optional[float]
    export_value: Optional[float]

class SMIPCSV:
    """
    CSV writer for SMIP (Simtricity Meter Import/Export) format files.

    This class handles writing profile log data to CSV files following the
    SMIP format conventions.
    """

    @staticmethod
    def write(
        serial: str,
        output_file_path: str,
        records: List[SMIPCSVRecord],
        element_marker: Optional[str] = None
    ) -> None:
        """
        Write records to a CSV file in SMIP format.

        Args:
            serial: Meter serial number
            output_file_path: Path to write the CSV file
            records: List of SMIPCSVRecord objects to write
            element_marker: Optional element marker ('A' or 'B') for twin element meters
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # Determine element marker enum if provided
        element = None
        if element_marker:
            if element_marker.upper() == 'A':
                element = ElementMarker.A
            elif element_marker.upper() == 'B':
                element = ElementMarker.B

        # Create SMIP filename
        # Extract date from first record (assuming all records are for the same day)
        if records:
            record_date = records[0].timestamp.date()
        else:
            # If no records, use today's date
            record_date = datetime.now().date()

        smip_filename = SMIPFilename(serial, record_date, element)
        filename = smip_filename.filename()

        # Full path for the CSV file
        full_csv_path = os.path.join(output_file_path, filename)

        # Write CSV file
        with open(full_csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            header = ['Timestamp', 'Import', 'Export']
            if element_marker:
                header.append('Element')
            writer.writerow(header)

            # Write records
            for record in records:
                row = [
                    record.timestamp.isoformat(),
                    str(record.import_value) if record.import_value is not None else '',
                    str(record.export_value) if record.export_value is not None else ''
                ]
                if element_marker:
                    row.append(element_marker)
                writer.writerow(row)

    @staticmethod
    def write_from_profile_records(
        serial: str,
        output_dir: str,
        profile_records: List[dict],
        date: datetime,
        element_marker: Optional[str] = None
    ) -> None:
        """
        Convert profile log records to SMIPCSV format and write to file.

        Args:
            serial: Meter serial number
            output_dir: Directory to write CSV file to
            profile_records: List of profile log records (dicts with timestamp, import_a, import_b, etc.)
            date: Date the records are for
            element_marker: Optional element marker ('A' or 'B')
        """
        # Convert profile records to SMIPCSV records
        csv_records = []
        for record in profile_records:
            # Convert timestamp to datetime if it's not already
            if isinstance(record['timestamp'], str):
                timestamp = datetime.fromisoformat(record['timestamp'])
            else:
                timestamp = record['timestamp']

            # For profile log 1, we typically have import values
            # For twin element meters, we need to handle A/B registers
            import_value = None
            if element_marker == 'A':
                import_value = record.get('import_a')
            elif element_marker == 'B':
                import_value = record.get('import_b')
            else:
                # For single element meters, use import_a or combined value
                import_value = record.get('import_a') or record.get('import')

            csv_records.append(SMIPCSVRecord(
                timestamp=timestamp,
                import_value=import_value,
                export_value=record.get('export')  # Export values if available
            ))

        # Write to CSV
        SMIPCSV.write(serial, output_dir, csv_records, element_marker)