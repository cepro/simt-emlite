#!/usr/bin/env python3
"""
Simple Profile Download Script

This script provides a basic implementation of profile log 1 downloading for a single day.
It takes CLI arguments for serial and date, and downloads profile log 1 data
in chunks for one day via the Emlite mediator.

Usage:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union, cast

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record

from simt_emlite.mediator.api_core import EmliteMediatorAPI
from simt_emlite.profile_logs.download_cache import (
    CachedLog1Record,
    CachedLog2Record,
    DownloadCache,
)

# mypy: disable-error-code="import-untyped"
from simt_emlite.smip.smip_file_finder import SMIPFileFinder
from simt_emlite.smip.smip_file_finder_result import SMIPFileFinderResult
from simt_emlite.smip.smip_filename import ElementMarker
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import (
    is_three_phase,
    is_twin_element,
)

logger = get_logger(__name__, __file__)


class ProfileDownloader:
    def __init__(
        self,
        date: datetime.date,
        output_dir: str = "output",
        serial: str | None = None,
        name: str | None = None,
        logging_level: int = logging.INFO,
    ) -> None:
        self.serial = serial
        self.name = name
        self.date = date
        self.logging_level = logging_level

        self.output_dir = output_dir
        self._validate_output_directory()

        config = load_config()
        self.mediator_server = cast(str | None, config["mediator_server"])
        self.future_date_detected: Optional[datetime.date] = None

        self._init_emlite_client()

        # Resolve serial from name if missing
        if not self.serial and self.name:
            self.serial = self._resolve_serial_from_name(self.name)

        if not self.serial:
            raise Exception("Must provide at least one of meter name or serial.")

        # Resolve hardware info and other metadata from mediator
        assert self.client is not None

        # Now that we have a serial, we can fetch detailed info if needed
        # but hardware() is enough for basic setup
        self.hardware = self.client.hardware(self.serial)
        self.is_twin_element = is_twin_element(self.hardware)

        if is_three_phase(self.hardware):
            error_msg = (
                f"Three-phase meters are not currently supported. "
                f"Meter {self.serial} has hardware type '{self.hardware}'."
            )
            logger.warning(error_msg)
            raise NotImplementedError(error_msg)

        logger.info(
            f"Found meter [{self.serial}]. "
            f"hardware=[{self.hardware}], is_twin_element=[{self.is_twin_element}]"
        )


    def _validate_output_directory(self):
        """Validate that the output directory exists and is writable, or can be created"""
        import os

        # Check if the path exists
        if os.path.exists(self.output_dir):
            # If it exists, it must be a directory
            if not os.path.isdir(self.output_dir):
                raise ValueError(
                    f"Output path '{self.output_dir}' exists but is not a directory. Please provide a directory path, not a file path."
                )
        else:
            # If it doesn't exist, try to create it
            try:
                os.makedirs(self.output_dir, exist_ok=True)
                logger.info(f"Created output directory: {self.output_dir}")
            except OSError as e:
                raise ValueError(
                    f"Cannot create output directory '{self.output_dir}': {e}. Please provide a valid directory path."
                )


    def _init_emlite_client(self):
        """Initialize the Emlite mediator client"""
        if not self.mediator_server:
            raise Exception("MEDIATOR_SERVER environment variable not set.")

        self.client = EmliteMediatorAPI(
            mediator_address=self.mediator_server,
            logging_level=self.logging_level,
        )

        logger.info(f"Connected to mediator at {self.mediator_server}")

    def _resolve_serial_from_name(self, name: str) -> str:
        """Resolve a meter name to a serial number using the mediator's meter list."""
        if not self.client:
            self._init_emlite_client()
        assert self.client is not None

        # Handle ESCO.NAME format
        parts = name.split(".", 1)
        esco_code: str | None = None
        search_name: str = name

        if len(parts) == 2:
            esco_code = parts[0].lower()
            search_name = parts[1]
            logger.debug(f"Searching for meter with ESCO [{esco_code}] and Name [{search_name}]")

        # Get meters list from mediator
        # If we have an ESCO code, use it to filter the list
        meters_json = self.client.grpc_client.get_meters(esco=esco_code)
        try:
            meters = json.loads(meters_json)
        except Exception as e:
            logger.error(f"Failed to parse meters JSON from mediator: {e}")
            raise Exception(f"Could not parse meter list from mediator: {e}")

        # Try to find match by name
        for meter in meters:
            # Match against the name segment (e.g. Plot-34.C)
            if meter.get("name") == search_name:
                serial = meter.get("serial")
                if serial:
                    logger.info(f"Resolved name [{name}] to serial [{serial}]")
                    # Update name to the one from the registry if needed,
                    # but keeping original for now.
                    return str(serial)

            # Also try matching against the full name if search_name didn't work
            if meter.get("name") == name:
                serial = meter.get("serial")
                if serial:
                    logger.info(f"Resolved full name [{name}] to serial [{serial}]")
                    return str(serial)

        raise Exception(f"Meter with name [{name}] not found in mediator registry.")

    def find_download_file(self) -> SMIPFileFinderResult:
        assert self.serial is not None

        output_path = Path(self.output_dir)
        if self.is_twin_element:
            find_result = SMIPFileFinder.find_with_element(
                output_path, self.serial, self.date, ElementMarker.A
            )
        else:
            find_result = SMIPFileFinder.find(output_path, self.serial, self.date)

        return find_result

    def download_profile_log_1_day(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
        cache: Optional[DownloadCache] = None,
    ) -> Dict[datetime.datetime, Any]:
        """Download profile log 1 data for a single day in chunks

        Args:
            progress_callback: Optional callback for progress updates
            cache: Optional DownloadCache for resumable downloads

        Returns:
            Dict of timestamp to profile log 1 record (EmopProfileLog1Record or CachedLog1Record)
        """

        # Convert date to datetime for the day (ensure timezone-aware)
        start_datetime = datetime.datetime.combine(
            self.date, datetime.time.min
        ).replace(tzinfo=datetime.timezone.utc)
        end_datetime = datetime.datetime.combine(self.date, datetime.time.max).replace(
            tzinfo=datetime.timezone.utc
        )

        logger.info(
            f"Downloading profile_log_1 data for {self.date}",
            name=self.name,
            serial=self.serial,
        )

        # Download in 2-hour chunks (4 x 30-minute intervals per chunk)
        current_time = start_datetime
        chunk_size = datetime.timedelta(hours=2)
        profile_records: Dict[datetime.datetime, Any] = {}

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)
            chunk_key = current_time.isoformat()

            # Check cache for this chunk
            if cache and cache.has_log1_chunk(chunk_key):
                msg = f"profile_log_1 chunk {current_time.strftime('%H:%M')} loaded from cache"
                logger.info(msg, name=self.name, serial=self.serial)
                if progress_callback:
                    progress_callback(msg)
                for ts, record in cache.get_log1_records().items():
                    if current_time <= ts < chunk_end:
                        profile_records[ts] = record
                current_time = chunk_end
                continue

            msg = f"Reading profile_log_1 chunk: {current_time.strftime('%H:%M')} to {chunk_end.strftime('%H:%M')}"
            logger.info(
                msg,
                name=self.name,
                serial=self.serial,
            )
            if progress_callback:
                progress_callback(msg)

            # Download profile log for this chunk
            assert self.client is not None
            assert self.serial is not None
            response = self.client.profile_log_1(self.serial, current_time)
            if response and response.records:
                logger.info(
                    f"Received {len(response.records)} records for {current_time}",
                    name=self.name,
                    serial=self.serial,
                )
                # future time out of range - see unfuddle #382 - meters will return the next
                # available data even if that is months ahead
                response_datetime = response.records[0].timestamp_datetime
                if response_datetime > end_datetime:
                    logger.warning(
                        "Future date returned - skipping remainder for this period",
                        name=self.name,
                        date=response_datetime,
                    )
                    self.future_date_detected = response_datetime.date()
                    return profile_records

                for record in response.records:
                    profile_records[record.timestamp_datetime] = record

                # Save chunk to cache
                if cache:
                    chunk_records = {
                        r.timestamp_datetime.isoformat(): {
                            "import_a": r.import_a,
                            "import_b": r.import_b,
                        }
                        for r in response.records
                    }
                    cache.save_log1_chunk(chunk_key, chunk_records)

            # Move to next chunk
            current_time = chunk_end

        logger.info("profile_log_1 download completed")

        return profile_records

    def download_profile_log_2_day(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
        cache: Optional[DownloadCache] = None,
    ) -> Dict[datetime.datetime, Any]:
        """Download profile log 2 data for a single day in chunks.

        Profile log 2 returns different numbers of records depending on meter type:
        - Twin element meters (hardware C1.w): 2 records per call (2 x 30 min = 1 hour)
        - Single element meters: 3 records per call (3 x 30 min = 1.5 hours)

        Args:
            progress_callback: Optional callback for progress updates
            cache: Optional DownloadCache for resumable downloads

        Returns:
            Dict of timestamp to profile log 2 record (EmopProfileLog2Record or CachedLog2Record)
        """

        # Convert date to datetime for the day (ensure timezone-aware)
        start_datetime = datetime.datetime.combine(
            self.date, datetime.time.min
        ).replace(tzinfo=datetime.timezone.utc)
        end_datetime = datetime.datetime.combine(self.date, datetime.time.max).replace(
            tzinfo=datetime.timezone.utc
        )

        # Chunk size depends on meter type:
        # - Twin element: 2 records per call = 1 hour (2 x 30 min intervals)
        # - Single element: 3 records per call = 1.5 hours (3 x 30 min intervals)
        if self.is_twin_element:
            chunk_size = datetime.timedelta(hours=1)
            records_per_chunk = 2
        else:
            chunk_size = datetime.timedelta(hours=1, minutes=30)
            records_per_chunk = 3

        logger.info(
            f"Downloading profile_log_2 data for {self.date} "
            f"(is_twin_element={self.is_twin_element}, records_per_chunk={records_per_chunk})"
        )

        current_time = start_datetime
        profile_records: Dict[datetime.datetime, Any] = {}

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)
            chunk_key = current_time.isoformat()

            # Check cache for this chunk
            if cache and cache.has_log2_chunk(chunk_key):
                msg = f"profile_log_2 chunk {current_time.strftime('%H:%M')} loaded from cache"
                logger.info(msg)
                if progress_callback:
                    progress_callback(msg)
                for ts, record in cache.get_log2_records().items():
                    if current_time <= ts < chunk_end:
                        profile_records[ts] = record
                current_time = chunk_end
                continue

            msg = f"Reading profile_log_2 chunk: {current_time.strftime('%H:%M')} to {chunk_end.strftime('%H:%M')}"
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

            assert self.client is not None
            assert self.serial is not None
            response = self.client.profile_log_2(self.serial, current_time, self.is_twin_element)
            if response and response.records:
                logger.info(
                    f"Received {len(response.records)} records for {current_time}"
                )
                # future time out of range - see unfuddle #382 - meters will return the next
                # available data even if that is months ahead
                response_datetime = response.records[0].timestamp_datetime
                if response_datetime > end_datetime:
                    logger.warning(
                        "Future date returned - skipping remainder for this period",
                        name=self.name,
                        date=response_datetime,
                    )
                    self.future_date_detected = response_datetime.date()
                    return profile_records

                for record in response.records:
                    profile_records[record.timestamp_datetime] = record

                # Save chunk to cache
                if cache:
                    chunk_records = {}
                    for r in response.records:
                        record_data: Dict[str, int] = {
                            "active_export_a": r.active_export_a,
                        }
                        if self.is_twin_element:
                            record_data["active_export_b"] = r.active_export_b
                        chunk_records[r.timestamp_datetime.isoformat()] = record_data
                    cache.save_log2_chunk(chunk_key, chunk_records)

            # Move to next chunk
            current_time = chunk_end

        logger.info("profile_log_2 download completed")

        return profile_records
