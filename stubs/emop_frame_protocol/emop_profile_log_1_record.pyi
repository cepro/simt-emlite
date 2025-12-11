"""Type stubs for emop_frame_protocol.emop_profile_log_1_record"""

from datetime import datetime
from typing import Any, Optional

from .generated.emop_profile_log_record_status import EmopProfileLogRecordStatus

class EmopProfileLog1Record:
    """Profile log type 1 record with convenience wrapper.

    Extends the generated record with a timestamp_datetime property.
    """

    _io: Any
    _parent: Any
    _root: Any

    # Record fields (from generated base class)
    timestamp: int
    """Timestamp as EMOP epoch seconds (seconds since 2000-01-01)"""

    status: EmopProfileLogRecordStatus
    """Status flags for this record"""

    import_a: int
    """Total active import for element A (Wh)"""

    import_b: int
    """Total active import for element B (Wh)"""

    @property
    def timestamp_datetime(self) -> datetime:
        """Timestamp converted to Python datetime"""
        ...

    def __init__(
        self,
        _io: Optional[Any] = None,
        _parent: Optional[Any] = None,
        _root: Optional[Any] = None,
    ) -> None: ...
    def _read(self) -> None: ...
    def _fetch_instances(self) -> None: ...
    def _write__seq(self, io: Optional[Any] = None) -> None: ...
    def _check(self) -> None: ...
    def __str__(self) -> str: ...
