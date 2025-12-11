#!/usr/bin/env python3
"""
Unit tests for ProfileDownloader conversion functionality
"""

import datetime
import unittest

from simt_emlite.profile_logs.profile_converter import convert_profile_records


class TestProfileDownloaderConversion(unittest.TestCase):
    """Test the profile record conversion functionality"""

    def test_convert_profile_records_successful_conversion(self):
        """Test successful conversion of raw profile records"""
        # Set up raw records with mock timestamps
        raw_records = [
            {
                "raw_timestamp": 1724234400,  # Unix timestamp for 2024-08-21 10:00:00 UTC
                "import_a": 100,
                "import_b": 200,
                "status": 0,
                "export": 50,
            },
            {
                "raw_timestamp": "2024-08-21T12:00:00Z",  # ISO format
                "import_a": 150,
                "import_b": 250,
                "status": 1,
            },
        ]

        converted_records = convert_profile_records(
            convert_profile_records(raw_records)
        )

        # Verify the conversion results
        self.assertEqual(len(converted_records), 2)

        # Check first record
        first_record = converted_records[0]
        self.assertEqual(
            first_record["timestamp"],
            datetime.datetime(2024, 8, 21, 10, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(first_record["import_a"], 100)
        self.assertEqual(first_record["import_b"], 200)
        self.assertEqual(first_record["status"], 0)

        # Check second record
        second_record = converted_records[1]
        self.assertEqual(
            second_record["timestamp"],
            datetime.datetime(2024, 8, 21, 12, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(second_record["import_a"], 150)
        self.assertEqual(second_record["import_b"], 250)
        self.assertEqual(second_record["status"], 1)

    def test_convert_profile_records_empty_list(self):
        """Test conversion with empty records list"""
        self.assertEqual(convert_profile_records([]), [])


if __name__ == "__main__":
    unittest.main()
