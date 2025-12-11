"""Type stubs for emop_frame_protocol.emop_profile_log_2_record"""

from datetime import datetime
from typing import Any, Optional

from .generated.emop_profile_log_record_status import EmopProfileLogRecordStatus

class EmopProfileLog2Record:
    """Profile log type 2 record with convenience wrapper.

    Extends the generated record with a timestamp_datetime property.
    """

    _io: Any
    _parent: Any
    _root: Any

    is_twin_element: bool
    """Whether meter has two elements"""

    # Record fields (from generated base class)
    timestamp: int
    """Timestamp as EMOP epoch seconds (seconds since 2000-01-01)"""

    status: EmopProfileLogRecordStatus
    """Status flags for this record"""

    active_export_a: int
    """Total active export for element A (Wh)"""

    reactive_import_a: int
    """Total reactive import for element A (VARh)"""

    reactive_export_a: int
    """Total reactive export for element A (VARh)"""

    voltage: int
    """Voltage reading"""

    # Twin element fields (only present if is_twin_element is True)
    active_export_b: int
    """Total active export for element B (Wh) - only for twin element meters"""

    reactive_import_b: int
    """Total reactive import for element B (VARh) - only for twin element meters"""

    reactive_export_b: int
    """Total reactive export for element B (VARh) - only for twin element meters"""

    @property
    def timestamp_datetime(self) -> datetime:
        """Timestamp converted to Python datetime"""
        ...

    def __init__(
        self,
        is_twin_element: bool,
        _io: Optional[Any] = None,
        _parent: Optional[Any] = None,
        _root: Optional[Any] = None,
    ) -> None: ...
    def _read(self) -> None: ...
    def _fetch_instances(self) -> None: ...
    def _write__seq(self, io: Optional[Any] = None) -> None: ...
    def _check(self) -> None: ...
    def __str__(self) -> str: ...
