#!/usr/bin/env python3
"""
Unit tests for timestamp utility functions
"""

import datetime
import pytest
from simt_emlite.util.timestamp import (
    convert_timestamp_to_datetime,
    parse_meter_timestamp,
    validate_timestamp_range,
    TimestampConversionError
)

class TestTimestampConversion:
    """Test timestamp conversion functions"""

    def test_datetime_passthrough(self):
        """Test that datetime objects are passed through unchanged"""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        result = convert_timestamp_to_datetime(dt)
        assert result == dt

    def test_naive_datetime_gets_timezone(self):
        """Test that naive datetimes get timezone added"""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        result = convert_timestamp_to_datetime(dt)
        assert result.tzinfo is not None
        assert result == dt.replace(tzinfo=datetime.timezone.utc)

    def test_unix_timestamp_conversion(self):
        """Test standard Unix timestamp conversion"""
        # Unix timestamp for 2023-01-15 10:30:00 UTC
        timestamp = 1673781000
        result = convert_timestamp_to_datetime(timestamp)
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_iso_string_conversion(self):
        """Test ISO 8601 string conversion"""
        iso_string = "2023-01-15T10:30:00+00:00"
        result = convert_timestamp_to_datetime(iso_string)
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_naive_iso_string_gets_timezone(self):
        """Test that naive ISO strings get timezone added"""
        iso_string = "2023-01-15T10:30:00"
        result = convert_timestamp_to_datetime(iso_string)
        assert result.tzinfo is not None
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_invalid_string_format(self):
        """Test that invalid string formats raise exception"""
        with pytest.raises(TimestampConversionError):
            convert_timestamp_to_datetime("invalid-date-format")

    def test_invalid_type(self):
        """Test that unsupported types raise exception"""
        with pytest.raises(TimestampConversionError):
            convert_timestamp_to_datetime(None)
        with pytest.raises(TimestampConversionError):
            convert_timestamp_to_datetime([])

    def test_meter_specific_timestamp_with_epoch_2000(self):
        """Test meter timestamp parsing with epoch 2000"""
        # 1000 seconds since 2000-01-01 should be 2000-01-01 00:16:40
        timestamp = 1000
        reference_date = datetime.date(2000, 1, 1)
        result = parse_meter_timestamp(timestamp, reference_date)
        expected = datetime.datetime(2000, 1, 1, 0, 16, 40, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_timestamp_validation_in_range(self):
        """Test timestamp validation for dates in expected range"""
        test_date = datetime.date(2023, 1, 15)
        timestamp = datetime.datetime(2023, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        assert validate_timestamp_range(timestamp, test_date, tolerance_days=1)

    def test_timestamp_validation_out_of_range(self):
        """Test timestamp validation for dates out of expected range"""
        test_date = datetime.date(2023, 1, 15)
        timestamp = datetime.datetime(2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
        assert not validate_timestamp_range(timestamp, test_date, tolerance_days=1)

    def test_float_timestamp_conversion(self):
        """Test conversion of float timestamps"""
        timestamp = 1673781000.5  # Unix timestamp with milliseconds
        result = convert_timestamp_to_datetime(timestamp)
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0, 500000, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_very_old_unix_timestamp(self):
        """Test conversion of very old Unix timestamps"""
        timestamp = 0  # Unix epoch
        result = convert_timestamp_to_datetime(timestamp)
        expected = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        assert result == expected

    def test_future_unix_timestamp(self):
        """Test conversion of future Unix timestamps"""
        # Unix timestamp for 2100-01-01
        timestamp = 4102444800
        result = convert_timestamp_to_datetime(timestamp)
        expected = datetime.datetime(2100, 1, 1, tzinfo=datetime.timezone.utc)
        assert result == expected

if __name__ == "__main__":
    pytest.main([__file__, "-v"])