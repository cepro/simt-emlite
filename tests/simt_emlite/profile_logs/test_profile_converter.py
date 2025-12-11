#!/usr/bin/env python3
"""
Unit tests for ProfileDownloader conversion functionality
"""

import datetime
import unittest

from simt_emlite.profile_logs.profile_converter import convert_profile_records


class MockStatus:
    """Mock implementation of EmopProfileLogRecordStatus"""

    def __init__(self):
        pass


class MockEmopProfileLog1Record:
    """Mock implementation of EmopProfileLog1Record for testing"""

    def __init__(self, timestamp, import_a, import_b, status=0):
        self.timestamp = timestamp
        self.import_a = import_a
        self.import_b = import_b
        self.status = status


class TestProfileDownloaderConversion(unittest.TestCase):
    """Test the profile record conversion functionality"""

    def test_convert_profile_records_successful_conversion(self):
        """Test successful conversion of raw profile records"""
        # Create mock EmopProfileLog1Record instances with exact timestamps
        raw_records = [
            MockEmopProfileLog1Record(
                timestamp=1724036800,  # Unix timestamp for 2024-08-21 10:00:00 UTC
                import_a=100,
                import_b=200,
                status=0,
            ),
            MockEmopProfileLog1Record(
                timestamp=1724044800,  # Unix timestamp for 2024-08-21 12:00:00 UTC
                import_a=150,
                import_b=250,
                status=1,
            ),
        ]

        converted_records = convert_profile_records(raw_records)

        # Verify the conversion results
        self.assertEqual(len(converted_records), 2)

        # Check first record
        first_record = converted_records[0]
        self.assertIsInstance(first_record["timestamp"], datetime.datetime)
        self.assertEqual(first_record["timestamp"].tzinfo, datetime.timezone.utc)
        self.assertEqual(first_record["import_a"], 100)
        self.assertEqual(first_record["import_b"], 200)
        self.assertEqual(first_record["status"], 0)

        # Check second record
        second_record = converted_records[1]
        self.assertIsInstance(second_record["timestamp"], datetime.datetime)
        self.assertEqual(second_record["timestamp"].tzinfo, datetime.timezone.utc)
        self.assertEqual(second_record["import_a"], 150)
        self.assertEqual(second_record["import_b"], 250)
        self.assertEqual(second_record["status"], 1)

    def test_convert_profile_records_empty_list(self):
        """Test conversion with empty records list"""
        self.assertEqual(convert_profile_records([]), [])


if __name__ == "__main__":
    unittest.main()
