import os
import tempfile
import unittest
from datetime import datetime

from emop_frame_protocol.emop_message import EmopMessage

from simt_emlite.util.three_phase_intervals import export_three_phase_intervals_to_csv


class TestThreePhaseIntervalsCSVExport(unittest.TestCase):
    """Unit tests for the ThreePhaseIntervals CSV export function."""

    def setUp(self):
        """Set up test fixtures before each test method."""

        # Mock the status class (since we don't have the actual implementation)
        class MockStatus:
            def __init__(self):
                self.valid_data = True
                self.power_fail = False
                self.phase_1_voltage_failure = True
                self.phase_2_voltage_failure = True
                self.phase_3_voltage_failure = False
                self.security_access = False
                self.md_reset = False
                self.time_update = False
                self.log_reset = False

        # Mock the interval record class
        class MockIntervalRecord:
            def __init__(self, values):
                self.channel_data = values
                self.status = MockStatus()

        # Mock the ThreePhaseIntervals class to avoid the tuple issue
        class MockThreePhaseIntervals:
            def __init__(
                self,
                block_start_time,
                interval_duration,
                num_channel_ids,
                channel_ids,
                intervals,
            ):
                self.block_start_time = block_start_time  # Store directly as datetime
                self.interval_duration = interval_duration
                self.num_channel_ids = num_channel_ids
                self.channel_ids = channel_ids
                self.intervals = intervals

        # Create test data matching the provided example
        self.test_record = MockThreePhaseIntervals(
            block_start_time=datetime(2025, 6, 2, 20, 0, 0),
            interval_duration=30,
            num_channel_ids=4,
            channel_ids=[0x010800, 0x020800, 0x030800, 0x040800],
            intervals=[
                MockIntervalRecord([4053, 1179, 2780, 149]),
                MockIntervalRecord([4053, 1179, 2780, 149]),
                MockIntervalRecord([4053, 1179, 2780, 149]),
            ],  # Using 3 intervals for simpler testing
        )

    def test_export_without_status_columns(self):
        """Test CSV export without status columns."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as tmp_file:
            csv_path = tmp_file.name

        try:
            # Export the data
            export_three_phase_intervals_to_csv(
                self.test_record,
                csv_path,
                EmopMessage.ThreePhaseMeterType.ax_whole_current,
                include_statuses=False,
            )

            # Read the CSV content
            with open(csv_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Expected content
            expected_lines = [
                "created_at,total_active_energy_import,total_active_energy_export,total_reactive_energy_import,total_reactive_energy_export",
                "2025-06-02T20:00:00,4.053,1.179,2.78,0.149",
                "2025-06-02T20:30:00,4.053,1.179,2.78,0.149",
                "2025-06-02T21:00:00,4.053,1.179,2.78,0.149",
            ]

            # Assert the content matches
            self.assertEqual(
                len(lines), len(expected_lines), "Number of lines doesn't match"
            )
            for i, (actual, expected) in enumerate(zip(lines, expected_lines)):
                self.assertEqual(actual, expected, f"Line {i + 1} doesn't match")

        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_export_with_status_columns(self):
        """Test CSV export with status columns."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as tmp_file:
            csv_path = tmp_file.name

        try:
            # Export the data with status columns
            export_three_phase_intervals_to_csv(
                self.test_record,
                csv_path,
                EmopMessage.ThreePhaseMeterType.ax_whole_current,
                include_statuses=True,
            )

            # Read the CSV content
            with open(csv_path, "r") as f:
                lines = f.read().strip().split("\n")

            # Expected header
            expected_header = "created_at,total_active_energy_import,total_active_energy_export,total_reactive_energy_import,total_reactive_energy_export,valid_data,power_fail,phase_1_voltage_failure,phase_2_voltage_failure,phase_3_voltage_failure,security_access,md_reset,time_update,log_reset"

            # Expected data rows
            expected_data_row = "2025-06-02T20:00:00,4.053,1.179,2.78,0.149,True,False,True,True,False,False,False,False,False"
            expected_lines = [
                expected_header,
                expected_data_row,
                "2025-06-02T20:30:00,4.053,1.179,2.78,0.149,True,False,True,True,False,False,False,False,False",
                "2025-06-02T21:00:00,4.053,1.179,2.78,0.149,True,False,True,True,False,False,False,False,False",
            ]

            # Assert the content matches
            self.assertEqual(
                len(lines), len(expected_lines), "Number of lines doesn't match"
            )
            for i, (actual, expected) in enumerate(zip(lines, expected_lines)):
                self.assertEqual(actual, expected, f"Line {i + 1} doesn't match")

        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)


if __name__ == "__main__":
    unittest.main()
