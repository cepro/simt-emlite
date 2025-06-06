from typing import List

from emop_frame_protocol.emop_profile_three_phase_interval_record import (
    EmopProfileThreePhaseIntervalRecord,
    emop_profile_three_phase_interval_record_pretty_print,
)
from emop_frame_protocol.util import emop_epoch_seconds_to_datetime


class ThreePhaseIntervals:
    """Simple data container for three phase profile interval block header values.
    Used for passing parsed header data around without the complexity of the Kaitai parser.
    """

    def __init__(
        self,
        block_start_time: int,
        interval_duration: int,
        num_channel_ids: int,
        channel_ids: List[int],
        intervals: List[EmopProfileThreePhaseIntervalRecord],
    ):
        self.block_start_time = emop_epoch_seconds_to_datetime(block_start_time)
        self.interval_duration = interval_duration
        self.num_channel_ids = num_channel_ids
        self.channel_ids = channel_ids
        self.intervals = intervals

    def __str__(self):
        channel_ids_str = ", ".join(channel_id.hex() for channel_id in self.channel_ids)
        intervals_str = ", ".join(
            emop_profile_three_phase_interval_record_pretty_print(record)
            for record in self.intervals
        )
        return (
            "EmopProfileThreePhaseIntervalsBlockHeader("
            f"block_start_time={self.block_start_time}, "
            f"interval_duration={self.interval_duration}, "
            f"num_channel_ids={self.num_channel_ids}, "
            f"channel_ids=({channel_ids_str}), "
            f"intervals=({intervals_str})"
            ")"
        )
