"""Type stubs for emop_frame_protocol.generated.emop_profile_log_1_record"""

from typing import Any, Optional

from .emop_profile_log_record_status import EmopProfileLogRecordStatus

class EmopProfileLog1Record:
    """Profile log type 1 record containing readings for a single half hour.

    Profile logs are a special type of message in the EMOP. The response for
    a profile log type 1 request is a fixed 80 bytes that contains 4 x 14 byte
    records.
    """

    _io: Any
    _parent: Any
    _root: Any

    # Record fields
    timestamp: int
    """Timestamp as EMOP epoch seconds (seconds since 2000-01-01)"""

    status: EmopProfileLogRecordStatus
    """Status flags for this record"""

    import_a: int
    """Total active import for element A (Wh)"""

    import_b: int
    """Total active import for element B (Wh)"""

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
