"""Type stubs for emop_frame_protocol.generated.emop_profile_log_2_record"""

from typing import Any, Optional

from .emop_profile_log_record_status import EmopProfileLogRecordStatus

class EmopProfileLog2Record:
    """Profile log type 2 record containing export/reactive readings.

    Profile logs are a special type of message in the EMOP. The response for
    a profile log type 2 request can take one of 2 forms depending on if the
    meter is twin element or not. Both will return 80 bytes however:
    - single elements return 3 x 22 byte records for 3 x half hourly periods
    - twin elements return 2 x 34 byte records for 2 x half hourly periods
    """

    _io: Any
    _parent: Any
    _root: Any

    is_twin_element: bool
    """Whether meter has two elements"""

    # Record fields
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
