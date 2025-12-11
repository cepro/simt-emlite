"""Type stubs for emop_frame_protocol.generated.emop_profile_log_record_status"""

from typing import Any, Optional

class EmopProfileLogRecordStatus:
    """Profile log records have 2 bytes reserved for setting status flags."""

    _io: Any
    _parent: Any
    _root: Any

    # Status flags
    unused_4: bool
    unused_5: bool
    unused_6: bool
    unused_7: bool
    unused_8: bool
    unused_9: bool
    unused_10: bool
    reset: bool
    valid_data: bool
    power_fail: bool
    minor_time_error: bool
    major_time_error: bool
    comms_error: bool
    unused_1: bool
    unused_2: bool
    unused_3: bool

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
