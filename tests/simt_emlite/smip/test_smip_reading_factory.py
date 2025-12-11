#!/usr/bin/env python3
"""
Tests for SMIP Reading Factory
"""

import datetime
import unittest
from dataclasses import dataclass


# Mock profile log records for testing
@dataclass
class MockLog1Record:
    """Mock profile log 1 record with import values"""
    timestamp: datetime.datetime
    total_active_import_a: float
    total_active_import_b: float


@dataclass
class MockLog2Record:
    """Mock profile log 2 record with export values"""
    timestamp: datetime.datetime
    total_active_export_a: float
    total_active_export_b: float


class TestCreateSmipReadingFromProfile(unittest.TestCase):
    """Tests for create_smip_reading_from_profile function"""

    def test_creates_reading_with_both_logs_element_a(self):
        """Should create reading with import from log1 and export from log2 for element A"""
        from simt_emlite.smip.smip_reading_factory import create_smip_reading_from_profile

        timestamp = datetime.datetime(2024, 8, 21, 10, 0, 0, tzinfo=datetime.timezone.utc)
        log1 = MockLog1Record(timestamp, 100.0, 200.0)
        log2 = MockLog2Record(timestamp, 50.0, 75.0)

        reading = create_smip_reading_from_profile(
            serial="EML1234567890",
            timestamp=timestamp,
            log1_record=log1,
            log2_record=log2,
            is_element_a=True
        )

        self.assertEqual(reading.serial, "EML1234567890")
        self.assertEqual(reading.register, 1)
        self.assertEqual(reading.timestamp, timestamp)
        self.assertEqual(reading.imp, 100.0)  # element A import
        self.assertEqual(reading.exp, 50.0)   # element A export
        self.assertEqual(reading.errorCode, 0)

    def test_creates_reading_with_both_logs_element_b(self):
        """Should create reading with import from log1 and export from log2 for element B"""
        from simt_emlite.smip.smip_reading_factory import create_smip_reading_from_profile

        timestamp = datetime.datetime(2024, 8, 21, 10, 0, 0, tzinfo=datetime.timezone.utc)
        log1 = MockLog1Record(timestamp, 100.0, 200.0)
        log2 = MockLog2Record(timestamp, 50.0, 75.0)

        reading = create_smip_reading_from_profile(
            serial="EML1234567890",
            timestamp=timestamp,
            log1_record=log1,
            log2_record=log2,
            is_element_a=False
        )

        self.assertEqual(reading.imp, 200.0)  # element B import
        self.assertEqual(reading.exp, 75.0)   # element B export

    def test_creates_reading_with_only_log1(self):
        """Should create reading with import value and None export when only log1 present"""
        from simt_emlite.smip.smip_reading_factory import create_smip_reading_from_profile

        timestamp = datetime.datetime(2024, 8, 21, 10, 0, 0, tzinfo=datetime.timezone.utc)
        log1 = MockLog1Record(timestamp, 100.0, 200.0)

        reading = create_smip_reading_from_profile(
            serial="EML1234567890",
            timestamp=timestamp,
            log1_record=log1,
            log2_record=None,
            is_element_a=True
        )

        self.assertEqual(reading.imp, 100.0)
        self.assertIsNone(reading.exp)

    def test_creates_reading_with_only_log2(self):
        """Should create reading with None import and export value when only log2 present"""
        from simt_emlite.smip.smip_reading_factory import create_smip_reading_from_profile

        timestamp = datetime.datetime(2024, 8, 21, 10, 0, 0, tzinfo=datetime.timezone.utc)
        log2 = MockLog2Record(timestamp, 50.0, 75.0)

        reading = create_smip_reading_from_profile(
            serial="EML1234567890",
            timestamp=timestamp,
            log1_record=None,
            log2_record=log2,
            is_element_a=True
        )

        self.assertIsNone(reading.imp)
        self.assertEqual(reading.exp, 50.0)


class TestCreateSmipReadings(unittest.TestCase):
    """Tests for create_smip_readings function"""

    def test_creates_readings_for_matching_timestamps(self):
        """Should create readings for timestamps with records"""
        from simt_emlite.smip.smip_reading_factory import create_smip_readings

        start = datetime.datetime(2024, 8, 21, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 8, 21, 2, 0, 0, tzinfo=datetime.timezone.utc)

        ts1 = start
        ts2 = start + datetime.timedelta(minutes=30)
        ts3 = start + datetime.timedelta(minutes=60)

        log1_records = {
            ts1: MockLog1Record(ts1, 100.0, 200.0),
            ts3: MockLog1Record(ts3, 300.0, 400.0),
        }
        log2_records = {
            ts1: MockLog2Record(ts1, 10.0, 20.0),
            ts2: MockLog2Record(ts2, 15.0, 25.0),
        }

        readings_a, readings_b = create_smip_readings(
            serial="EML1234567890",
            start_time=start,
            end_time=end,
            log1_records=log1_records,
            log2_records=log2_records,
            is_twin_element=False
        )

        # Should have 3 readings (ts1, ts2, ts3 all have at least one log)
        self.assertEqual(len(readings_a), 3)
        self.assertEqual(len(readings_b), 0)  # Not twin element

        # ts1 has both logs
        self.assertEqual(readings_a[0].timestamp, ts1)
        self.assertEqual(readings_a[0].imp, 100.0)
        self.assertEqual(readings_a[0].exp, 10.0)

        # ts2 only has log2
        self.assertEqual(readings_a[1].timestamp, ts2)
        self.assertIsNone(readings_a[1].imp)
        self.assertEqual(readings_a[1].exp, 15.0)

        # ts3 only has log1
        self.assertEqual(readings_a[2].timestamp, ts3)
        self.assertEqual(readings_a[2].imp, 300.0)
        self.assertIsNone(readings_a[2].exp)

    def test_creates_readings_for_twin_element(self):
        """Should create both A and B readings for twin element meters"""
        from simt_emlite.smip.smip_reading_factory import create_smip_readings

        start = datetime.datetime(2024, 8, 21, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 8, 21, 1, 0, 0, tzinfo=datetime.timezone.utc)

        ts1 = start

        log1_records = {
            ts1: MockLog1Record(ts1, 100.0, 200.0),
        }
        log2_records = {
            ts1: MockLog2Record(ts1, 10.0, 20.0),
        }

        readings_a, readings_b = create_smip_readings(
            serial="EML1234567890",
            start_time=start,
            end_time=end,
            log1_records=log1_records,
            log2_records=log2_records,
            is_twin_element=True
        )

        self.assertEqual(len(readings_a), 1)
        self.assertEqual(len(readings_b), 1)

        # Element A
        self.assertEqual(readings_a[0].imp, 100.0)
        self.assertEqual(readings_a[0].exp, 10.0)

        # Element B
        self.assertEqual(readings_b[0].imp, 200.0)
        self.assertEqual(readings_b[0].exp, 20.0)

    def test_skips_timestamps_without_records(self):
        """Should skip timestamps that have no records in either log"""
        from simt_emlite.smip.smip_reading_factory import create_smip_readings

        start = datetime.datetime(2024, 8, 21, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 8, 21, 2, 0, 0, tzinfo=datetime.timezone.utc)

        # Only one record at a specific time
        ts = start + datetime.timedelta(minutes=30)
        log1_records = {
            ts: MockLog1Record(ts, 100.0, 200.0),
        }
        log2_records = {}

        readings_a, _ = create_smip_readings(
            serial="EML1234567890",
            start_time=start,
            end_time=end,
            log1_records=log1_records,
            log2_records=log2_records,
            is_twin_element=False
        )

        # Should only have 1 reading (for ts at 00:30)
        self.assertEqual(len(readings_a), 1)
        self.assertEqual(readings_a[0].timestamp, ts)

    def test_empty_records(self):
        """Should return empty lists when no records exist"""
        from simt_emlite.smip.smip_reading_factory import create_smip_readings

        start = datetime.datetime(2024, 8, 21, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 8, 21, 1, 0, 0, tzinfo=datetime.timezone.utc)

        readings_a, readings_b = create_smip_readings(
            serial="EML1234567890",
            start_time=start,
            end_time=end,
            log1_records={},
            log2_records={},
            is_twin_element=False
        )

        self.assertEqual(len(readings_a), 0)
        self.assertEqual(len(readings_b), 0)


if __name__ == "__main__":
    unittest.main()
