#!/usr/bin/env python3
"""
SMIPCSV implementation based on Java SMIPCSV class

This class handles writing profile log data to CSV files in the SMIP format.
"""

import csv
import datetime
import os
from typing import List, Optional

from .smip_csv_record import SMIPCSVRecord
from .smip_filename import ElementMarker, SMIPFilename
from .smip_reading import SMIPReading


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
        element_marker: Optional[str] = None,
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
        os.makedirs(output_file_path, exist_ok=True)

        # Determine element marker enum if provided
        element = None
        if element_marker:
            if element_marker.upper() == "A":
                element = ElementMarker.A
            elif element_marker.upper() == "B":
                element = ElementMarker.B

        # Create SMIP filename
        # Extract date from first record (assuming all records are for the same day)
        if records:
            record_date = records[0].timestamp.date()
        else:
            # If no records, use today's date
            record_date = datetime.datetime.now().date()

        smip_filename = SMIPFilename(serial, record_date, element)
        filename = smip_filename.filename()

        # Full path for the CSV file
        full_csv_path = os.path.join(output_file_path, filename)

        # Write CSV file
        with open(full_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            header = ["Timestamp", "Import", "Export"]
            if element_marker:
                header.append("Element")
            writer.writerow(header)

            # Write records
            for record in records:
                row = [
                    record.timestamp.isoformat(),
                    str(record.import_value) if record.import_value is not None else "",
                    str(record.export_value) if record.export_value is not None else "",
                ]
                if element_marker:
                    row.append(element_marker)
                writer.writerow(row)

    @staticmethod
    def write_from_profile_records(
        serial: str,
        output_dir: str,
        profile_records: List[dict],
        date: datetime.date,
        element_marker: Optional[str] = None,
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
            if isinstance(record["timestamp"], str):
                timestamp = datetime.datetime.fromisoformat(record["timestamp"])
            else:
                timestamp = record["timestamp"]

            # For profile log 1, we typically have import values
            # For twin element meters, we need to handle A/B registers
            import_a = record.get("import_a")
            import_b = record.get("import_b")

            if element_marker == "A":
                # Single element A meter - use import_a
                if import_a is not None:
                    csv_records.append(
                        SMIPCSVRecord(
                            timestamp=timestamp,
                            import_value=import_a,
                            export_value=record.get(
                                "export"
                            ),  # Export values if available
                        )
                    )
            elif element_marker == "B":
                # Single element B meter - use import_b
                if import_b is not None:
                    csv_records.append(
                        SMIPCSVRecord(
                            timestamp=timestamp,
                            import_value=import_b,
                            export_value=record.get(
                                "export"
                            ),  # Export values if available
                        )
                    )
            else:
                # No element marker specified - prioritize import_a, but include import_b if available
                # For meters with both import_a and import_b, include both values
                if import_a is not None:
                    csv_records.append(
                        SMIPCSVRecord(
                            timestamp=timestamp,
                            import_value=import_a,
                            export_value=record.get(
                                "export"
                            ),  # Export values if available
                        )
                    )

                # Also include import_b as a separate record if it's different from import_a
                # This handles twin element meters where both registers have meaningful data
                if import_b is not None and import_b != import_a:
                    csv_records.append(
                        SMIPCSVRecord(
                            timestamp=timestamp,
                            import_value=import_b,
                            export_value=record.get(
                                "export"
                            ),  # Export values if available
                        )
                    )

        # Write to CSV
        SMIPCSV.write(serial, output_dir, csv_records, element_marker)

    @staticmethod
    def read(csv_string: str) -> List[SMIPCSVRecord]:
        """
        Read records from a CSV string in SMIP format.

        Args:
            csv_string: CSV data as a string

        Returns:
            List of SMIPCSVRecord objects
        """
        import io

        return SMIPCSV._read_internal(io.StringIO(csv_string))

    @staticmethod
    def read_from_file(file_path: str) -> List[SMIPCSVRecord]:
        """
        Read records from a CSV file in SMIP format.

        Args:
            file_path: Path to CSV file

        Returns:
            List of SMIPCSVRecord objects
        """
        with open(file_path, "r") as file:
            return SMIPCSV._read_internal(file)

    @staticmethod
    def _read_internal(file_obj) -> List[SMIPCSVRecord]:
        """
        Internal method to read records from a file-like object.

        Args:
            file_obj: File-like object to read from

        Returns:
            List of SMIPCSVRecord objects
        """
        records = []

        # Read and discard the header line
        file_obj.readline()

        for line in file_obj:
            line = line.strip()
            if not line:
                continue

            # Parse the CSV line
            parts = line.split(",")
            if len(parts) < 3:
                continue

            timestamp_str = parts[0].strip('"')
            import_str = parts[1]
            export_str = parts[2]

            # Skip records with NA values
            if (
                import_str == SMIPCSVRecord.NA_VALUE
                or export_str == SMIPCSVRecord.NA_VALUE
            ):
                continue

            # Skip records with -1 values
            if import_str == "-1" or export_str == "-1":
                continue

            try:
                # Parse timestamp
                timestamp = datetime.datetime.strptime(
                    timestamp_str, SMIPCSVRecord.TIMESTAMP_FORMAT
                )

                # Convert values from Wh to kWh (divide by 1000)
                import_value = float(import_str) / 1000.0
                export_value = float(export_str) / 1000.0

                # Create record
                record = SMIPCSVRecord(
                    timestamp=timestamp,
                    import_value=import_value,
                    export_value=export_value,
                )
                records.append(record)

            except (ValueError, IndexError):
                # Skip malformed records
                continue

        return records

    @staticmethod
    def write_from_smip_readings(
        serial: str,
        output_dir: str,
        readings: List[SMIPReading],
        element_marker: Optional[str] = None,
    ) -> None:
        """
        Write SMIPReading objects to a CSV file in SMIP format.

        Converts SMIPReading objects to SMIPCSVRecord objects and writes them to a file.

        Args:
            serial: Meter serial number
            output_dir: Directory to write CSV file to
            readings: List of SMIPReading objects to write
            element_marker: Optional element marker ('A' or 'B') for twin element meters
        """
        # Convert SMIPReading objects to SMIPCSVRecord objects
        csv_records = [
            SMIPCSVRecord(
                timestamp=reading.timestamp,
                import_value=reading.imp,
                export_value=reading.exp,
            )
            for reading in readings
        ]

        # Write to CSV using the existing write method
        SMIPCSV.write(serial, output_dir, csv_records, element_marker)
