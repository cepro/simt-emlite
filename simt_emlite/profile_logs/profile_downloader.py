#!/usr/bin/env python3
"""
Simple Profile Download Script

This script provides a basic implementation of profile log 1 downloading for a single day.
It takes CLI arguments for serial and date, uses Supabase to get meter info,
and downloads profile log 1 data in chunks for one day.

Usage:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21
"""

import datetime
import logging
from pathlib import Path
from typing import Callable, Dict, Optional, cast

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record
from supabase import Client as SupabaseClient

from simt_emlite.mediator.client import EmliteMediatorClient

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
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

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
        self.supabase_url = config["supabase_url"]
        self.supabase_anon_key = config["supabase_anon_key"]
        self.supabase_access_token = config["supabase_access_token"]
        self.fly_region = config["fly_region"]
        self.env = config["env"]
        self.mediator_server = cast(str | None, config["mediator_server"])

        self.future_date_detected: Optional[datetime.date] = None

        self._check_config_and_args()

        self.client: EmliteMediatorClient | None = None
        self.supabase: SupabaseClient = self._init_supabase()

        self._fetch_meter_info()
        self._fetch_esco_code()

    def _check_config_and_args(self):
        if self.name is None and self.serial is None:
            raise Exception("Must provide at least one of meter name or serial.")

        if not all(
            [self.supabase_url, self.supabase_anon_key, self.supabase_access_token]
        ):
            raise Exception(
                "Environment variables SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_ACCESS_TOKEN not set."
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

    def _init_supabase(self) -> SupabaseClient:
        """Initialize Supabase client and get meter info"""
        if not all(
            [self.supabase_url, self.supabase_anon_key, self.supabase_access_token]
        ):
            raise Exception(
                "SUPABASE_URL, SUPABASE_ANON_KEY and/or SUPABASE_ACCESS_TOKEN not set"
            )

        # Narrow types after environment check
        assert self.supabase_url is not None
        assert self.supabase_anon_key is not None
        assert self.supabase_access_token is not None

        return supa_client(
            str(self.supabase_url),
            str(self.supabase_anon_key),
            str(self.supabase_access_token),
        )

    def _fetch_meter_info(self):
        query = self.supabase.table("meter_registry").select(
            "id,esco,hardware,serial,name"
        )
        if self.serial:
            query.eq("serial", self.serial)
        else:
            query.eq("name", self.name)
        result = query.execute()

        if len(as_list(result)) == 0:
            raise Exception(
                f"Meter not found in registry for serial=[{self.serial}]. name=[{self.name}]."
            )

        meter_data = as_first_item(result)
        self.meter_id = meter_data["id"]
        self.esco_id = meter_data["esco"]
        self.name = meter_data["name"]
        self.serial = meter_data["serial"]
        self.hardware: str = meter_data.get("hardware", "")
        self.is_twin_element: bool = is_twin_element(self.hardware)

        if is_three_phase(self.hardware):
            error_msg = (
                f"Three-phase meters are not currently supported. "
                f"Meter {self.serial} has hardware type '{self.hardware}'."
            )
            logger.warning(error_msg)
            raise NotImplementedError(error_msg)

        logger.info(
            f"Found meter [{self.serial}]. id: [{self.meter_id}], "
            f"hardware=[{self.hardware}], is_twin_element=[{self.is_twin_element}]"
        )

    def _fetch_esco_code(self):
        self.esco_code = None
        if self.esco_id is not None:
            result = (
                self.supabase.schema("flows")
                .table("escos")
                .select("code")
                .eq("id", self.esco_id)
                .execute()
            )
            self.esco_code = as_first_item(result)["code"] if as_list(result) else None
            logger.info(f"Found esco_code [{self.esco_code}] for esco [{self.esco_id}]")

    def _init_emlite_client(self):
        """Initialize the Emlite mediator client"""
        if not self.mediator_server:
            raise Exception("MEDIATOR_SERVER environment variable not set.")

        self.client = EmliteMediatorClient(
            mediator_address=self.mediator_server,
            logging_level=self.logging_level,
        )

        logger.info(f"Connected to mediator at {self.mediator_server}")

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
    ) -> Dict[datetime.datetime, EmopProfileLog1Record]:
        """Download profile log 1 data for a single day in chunks

        Returns:
            Dict of timestamp to profile log 1 record
        """
        if not self.client:
            self._init_emlite_client()

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
        profile_records: Dict[datetime.datetime, EmopProfileLog1Record] = {}

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)

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

            # Move to next chunk
            current_time = chunk_end

        logger.info("profile_log_1 download completed")

        return profile_records

    def download_profile_log_2_day(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[datetime.datetime, EmopProfileLog2Record]:
        """Download profile log 2 data for a single day in chunks.

        Profile log 2 returns different numbers of records depending on meter type:
        - Twin element meters (hardware C1.w): 2 records per call (2 x 30 min = 1 hour)
        - Single element meters: 3 records per call (3 x 30 min = 1.5 hours)

        Returns:
            Dict of timestamp to profile log 2 record
        """
        if not self.client:
            self._init_emlite_client()

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
        profile_records: Dict[datetime.datetime, EmopProfileLog2Record] = {}

        while current_time < end_datetime:
            chunk_end = min(current_time + chunk_size, end_datetime)

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

            # Move to next chunk
            current_time = chunk_end

        logger.info("profile_log_2 download completed")

        return profile_records
