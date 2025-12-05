#!/usr/bin/env python3
"""
Timestamp Utility Library

This utility provides robust timestamp conversion functions for handling
various timestamp formats commonly encountered in meter data.
"""

import datetime
import logging
from typing import Union, Optional

logger = logging.getLogger(__name__)

class TimestampConversionError(Exception):
    """Exception raised when timestamp conversion fails"""
    pass

def convert_timestamp_to_datetime(
    timestamp: Union[int, float, str, datetime.datetime],
    default_timezone: Optional[datetime.tzinfo] = datetime.timezone.utc
) -> datetime.datetime:
    """
    Convert various timestamp formats to datetime object.

    Supports:
    - datetime objects (passed through)
    - Unix timestamps (seconds since 1970-01-01)
    - ISO 8601 strings
    - Custom meter timestamp formats

    Args:
        timestamp: The timestamp to convert
        default_timezone: Timezone to use for naive datetimes

    Returns:
        datetime.datetime object

    Raises:
        TimestampConversionError: If conversion fails
    """
    # If already a datetime object, return as-is
    if isinstance(timestamp, datetime.datetime):
        # If naive datetime, add timezone
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=default_timezone)
        return timestamp

    # Handle string timestamps (ISO 8601 format)
    if isinstance(timestamp, str):
        try:
            # Try ISO 8601 format first
            dt = datetime.datetime.fromisoformat(timestamp)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=default_timezone)
            return dt
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse string timestamp '{timestamp}': {e}")
            raise TimestampConversionError(f"Cannot parse string timestamp: {timestamp}") from e

    # Handle numeric timestamps (could be Unix timestamp or other formats)
    if isinstance(timestamp, (int, float)):
        try:
            # Try standard Unix timestamp (seconds since 1970-01-01)
            # Force UTC timezone for consistency
            utc_timezone = datetime.timezone.utc
            dt = datetime.datetime.fromtimestamp(timestamp, utc_timezone)

            # Check if the resulting date is reasonable (not way in future/past)
            current_year = datetime.datetime.now(utc_timezone).year
            if abs(dt.year - current_year) > 50:  # More than 50 years difference
                logger.warning(f"Unix timestamp {timestamp} converted to unusual date: {dt}")
                # This might not be a Unix timestamp, try alternative interpretations

            return dt
        except (ValueError, OSError) as e:
            logger.debug(f"Failed to convert numeric timestamp {timestamp}: {e}")
            raise TimestampConversionError(f"Cannot convert numeric timestamp: {timestamp}") from e

    raise TimestampConversionError(f"Unsupported timestamp type: {type(timestamp)}")

def parse_meter_timestamp(
    timestamp_value: Union[int, float, str, datetime.datetime],
    reference_date: Optional[datetime.date] = None
) -> datetime.datetime:
    """
    Parse meter timestamps with special handling for meter-specific formats.

    Some meters use custom timestamp formats that need special interpretation.

    Args:
        timestamp_value: The timestamp value from meter data
        reference_date: Optional reference date for context

    Returns:
        datetime.datetime object
    """
    try:
        # First try standard conversion
        result = convert_timestamp_to_datetime(timestamp_value)

        # Check if the result seems unreasonable and we have a reference date
        if reference_date and isinstance(timestamp_value, (int, float)):
            current_year = datetime.datetime.now(datetime.timezone.utc).year
            if abs(result.year - current_year) > 50:  # More than 50 years difference
                # Result is unreasonable, try meter-specific formats
                logger.debug(f"Standard conversion gave unreasonable date {result}, trying meter-specific formats")

                # Handle case where timestamp might be seconds since some other epoch
                if isinstance(timestamp_value, (int, float)):
                    try:
                        # Try interpreting as seconds since 2000-01-01 (common in some meters)
                        epoch_2000 = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
                        dt = epoch_2000 + datetime.timedelta(seconds=timestamp_value)

                        # Check if result is reasonable
                        if reference_date:
                            date_diff = abs((dt.date() - reference_date).days)
                            if date_diff > 365:  # More than a year difference
                                logger.warning(f"Meter timestamp {timestamp_value} with epoch 2000 gives date {dt.date()}, expected around {reference_date}")
                        return dt
                    except Exception as e:
                        logger.debug(f"Failed meter-specific timestamp parsing: {e}")
                        raise TimestampConversionError(f"Cannot parse meter timestamp: {timestamp_value}") from e

        return result
    except TimestampConversionError:
        # If standard conversion fails, try meter-specific formats
        logger.debug(f"Trying meter-specific timestamp parsing for: {timestamp_value}")

        # Handle case where timestamp might be seconds since some other epoch
        if isinstance(timestamp_value, (int, float)):
            try:
                # Try interpreting as seconds since 2000-01-01 (common in some meters)
                epoch_2000 = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
                dt = epoch_2000 + datetime.timedelta(seconds=timestamp_value)

                # Check if result is reasonable
                if reference_date:
                    date_diff = abs((dt.date() - reference_date).days)
                    if date_diff > 365:  # More than a year difference
                        logger.warning(f"Meter timestamp {timestamp_value} with epoch 2000 gives date {dt.date()}, expected around {reference_date}")
                return dt
            except Exception as e:
                logger.debug(f"Failed meter-specific timestamp parsing: {e}")
                raise TimestampConversionError(f"Cannot parse meter timestamp: {timestamp_value}") from e

        raise TimestampConversionError(f"Cannot parse meter timestamp: {timestamp_value}")

def validate_timestamp_range(
    timestamp: datetime.datetime,
    expected_date: datetime.date,
    tolerance_days: int = 1
) -> bool:
    """
    Validate that a timestamp is within expected range.

    Args:
        timestamp: The timestamp to validate
        expected_date: The expected date
        tolerance_days: Allowed days difference

    Returns:
        bool: True if timestamp is within range
    """
    if not isinstance(timestamp, datetime.datetime):
        return False

    date_diff = abs((timestamp.date() - expected_date).days)
    return date_diff <= tolerance_days