# mypy: disable-error-code="import-untyped"
"""
Management API for Emlite meter operations.

This module provides methods for listing meters, getting meter info,
and querying meter clock drift status.
"""
import datetime
import logging
from typing import Any, Dict, TypedDict

import grpc

from simt_emlite.util.logging import get_logger

from .grpc.client import EmliteMediatorGrpcClient
from .mediator_client_exception import MediatorClientException

logger = get_logger(__name__, __file__)


class MeterClockDriftInfo(TypedDict):
    """Type definition for meter clock drift information."""

    serial: str
    clock_time_diff_seconds: int | None
    clock_time_diff_synced_at: str | None
    clock_time_diff_synced_at_formatted: str | None


class EmliteMeterManagementAPI:
    """
    API client for Emlite meter management operations.

    This class provides methods for listing meters, getting meter info,
    and querying meter clock drift status.
    """

    def __init__(
        self,
        mediator_address: str | None = "0.0.0.0:50051",
        logging_level: str | int = logging.INFO,
    ) -> None:
        self.grpc_client = EmliteMediatorGrpcClient(
            mediator_address=mediator_address,
        )

        logging.getLogger().setLevel(logging_level)

        global logger
        self.log = logger.bind(mediator_address=mediator_address)
        self.log.debug("EmliteMeterManagementAPI init")

    def meter_list(self, esco: str | None = None) -> str:
        """
        Get a list of all meters.

        Args:
            esco: Optional ESCO code to filter by (e.g. "wlce").

        Returns:
            JSON string containing meter list.
        """
        data = self.grpc_client.get_meters(esco=esco)
        self.log.info("received meters list", esco=esco)
        return data

    def meter_info(self, serial: str) -> str:
        """
        Get detailed info for a specific meter.

        Args:
            serial: Meter serial number.

        Returns:
            JSON string containing meter info.
        """
        data = self.grpc_client.get_info(serial)
        self.log.info("received info", serial=serial)
        return data

    def meter_clock_drift(self, serial: str) -> MeterClockDriftInfo:
        """
        Get clock drift information for a specific meter.

        Returns the current clock time drift in seconds and when it was
        last synced/captured.

        Args:
            serial: Meter serial number.

        Returns:
            Dictionary containing:
            - serial: Meter serial number
            - clock_time_diff_seconds: Clock drift in seconds (None if unknown)
            - clock_time_diff_synced_at: ISO timestamp when drift was captured (None if unknown)
            - clock_time_diff_synced_at_formatted: Human-readable timestamp (None if unknown)
        """
        try:
            import json

            info_json = self.grpc_client.get_info(serial)
            info_data: Dict[str, Any] = json.loads(info_json)

            drift_raw = info_data.get("clock_time_diff_seconds")
            last_read_raw = info_data.get("clock_time_diff_synced_at")

            # Format the timestamp if available
            last_read_formatted: str | None = None
            if last_read_raw:
                try:
                    dt = datetime.datetime.fromisoformat(
                        last_read_raw.replace("Z", "+00:00")
                    )
                    last_read_formatted = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except Exception as e:
                    self.log.warning(
                        f"Failed to parse capture timestamp '{last_read_raw}': {e}"
                    )

            result: MeterClockDriftInfo = {
                "serial": serial,
                "clock_time_diff_seconds": drift_raw,
                "clock_time_diff_synced_at": last_read_raw,
                "clock_time_diff_synced_at_formatted": last_read_formatted,
            }

            self.log.info("received clock drift info", serial=serial, result=result)
            return result

        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, str(e.details() or ""))
