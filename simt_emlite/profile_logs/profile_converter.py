#!/usr/bin/env python3
"""
Profile Converter Module

This module provides functions to convert raw profile log records to a final format for CSV writing.
"""

from typing import List

# mypy: disable-error-code="import-untyped"
from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.util import emop_epoch_seconds_to_datetime

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


def convert_profile_records(raw_records: List[EmopProfileLog1Record]) -> List[dict]:
    """Convert all collected raw profile records to final format for CSV writing"""
    if not raw_records:
        logger.warning("No profile records to convert")
        return []

    converted_records = []
    raw_record: EmopProfileLog1Record
    for raw_record in raw_records:
        converted_record = {
            "timestamp": emop_epoch_seconds_to_datetime(raw_record.timestamp),
            "import_a": raw_record.import_a,
            "import_b": raw_record.import_b,
            "status": raw_record.status,
            "export": getattr(raw_record, "export", None),
        }
        converted_records.append(converted_record)

    return converted_records
