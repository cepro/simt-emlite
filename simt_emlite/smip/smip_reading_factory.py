"""
SMIP Reading Factory

Creates SMIPReading objects from profile log records.
"""

import datetime
from typing import Dict, List, Optional, Tuple

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record

from .smip_reading import SMIPReading


def create_smip_reading_from_profile(
    serial: str,
    timestamp: datetime.datetime,
    log1_record: Optional[EmopProfileLog1Record],
    log2_record: Optional[EmopProfileLog2Record],
    is_element_a: bool,
) -> SMIPReading:
    """
    Create an SMIPReading from profile log 1 and log 2 records.

    Args:
        serial: Meter serial number
        timestamp: Record timestamp
        log1_record: Profile log 1 record (contains import values)
        log2_record: Profile log 2 record (contains export values)
        is_element_a: True for element A values, False for element B values

    Returns:
        SMIPReading with import/export values or None for missing data
    """
    import_value: Optional[float] = None
    if log1_record is not None:
        import_value = float(
            log1_record.import_a
            if is_element_a
            else log1_record.import_b
        )

    export_value: Optional[float] = None
    if log2_record is not None:
        export_value = float(
            log2_record.active_export_a
            if is_element_a
            else log2_record.active_export_b
        )

    return SMIPReading(
        serial=serial,
        register=1,
        timestamp=timestamp,
        imp=import_value,  # type: ignore[arg-type]
        exp=export_value,  # type: ignore[arg-type]
        errorCode=0,
    )


def create_smip_readings(
    serial: str,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    log1_records: Dict[datetime.datetime, EmopProfileLog1Record],
    log2_records: Dict[datetime.datetime, EmopProfileLog2Record],
    is_twin_element: bool = False,
    interval_minutes: int = 30,
) -> Tuple[List[SMIPReading], List[SMIPReading]]:
    """
    Create SMIP readings from profile log 1 and log 2 records.

    Iterates through timestamps from start_time to end_time, looking up
    log1 and log2 records for each timestamp. Creates SMIPReading objects
    for any timestamp that has at least one log record.

    Args:
        serial: Meter serial number
        start_time: Start of time range
        end_time: End of time range
        log1_records: Dict of timestamp -> profile log 1 record
        log2_records: Dict of timestamp -> profile log 2 record
        is_twin_element: True if meter has two elements (A and B)
        interval_minutes: Interval between readings in minutes (default 30)

    Returns:
        Tuple of (readings_a, readings_b) where readings_b is empty if not twin element
    """
    readings_a: List[SMIPReading] = []
    readings_b: List[SMIPReading] = []

    interval = datetime.timedelta(minutes=interval_minutes)
    record_timestamp = start_time

    while record_timestamp < end_time:
        log1_record = log1_records.get(record_timestamp)
        log2_record = log2_records.get(record_timestamp)

        # Add a reading only if there is data for at least 1 of the logs
        if log1_record is not None or log2_record is not None:
            readings_a.append(
                create_smip_reading_from_profile(
                    serial, record_timestamp, log1_record, log2_record, is_element_a=True
                )
            )

            if is_twin_element:
                readings_b.append(
                    create_smip_reading_from_profile(
                        serial,
                        record_timestamp,
                        log1_record,
                        log2_record,
                        is_element_a=False,
                    )
                )

        record_timestamp += interval

    return readings_a, readings_b
