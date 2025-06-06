import csv
from datetime import timedelta

from simt_emlite.dto.three_phase_intervals import ThreePhaseIntervals


def export_three_phase_intervals_to_csv(
    record: ThreePhaseIntervals, csv_file_path: str, include_statuses: bool = False
) -> None:
    """
    Export ThreePhaseIntervals record to CSV file.

    Args:
        record: ThreePhaseIntervals instance to export
        csv_file_path: Path where CSV file will be written
        include_statuses: If True, include status columns in the output
    """

    start_time = record.block_start_time

    # Prepare column headers
    headers = ["created_at"]

    # Add channel ID columns (convert hex IDs to strings for column names)
    channel_headers = []
    for channel_id in record.channel_ids:
        if isinstance(channel_id, int):
            # Convert integer to hex string
            channel_header = f"{channel_id:06x}"
        else:
            # Assume it's already a hex string or bytes
            channel_header = (
                channel_id.hex() if hasattr(channel_id, "hex") else str(channel_id)
            )
        channel_headers.append(channel_header)

    headers.extend(channel_headers)

    # Add status columns if requested
    status_headers = []
    if include_statuses and record.intervals:
        status_headers = [
            "valid_data",
            "power_fail",
            "phase_1_voltage_failure",
            "phase_2_voltage_failure",
            "phase_3_voltage_failure",
            "security_access",
            "md_reset",
            "time_update",
            "log_reset",
        ]
        headers.extend(status_headers)

    # Write CSV file
    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow(headers)

        for i, interval in enumerate(record.intervals):
            interval_time = start_time + timedelta(minutes=record.interval_duration * i)

            # Start building the row
            row = [interval_time.isoformat()]

            # Add channel values
            if len(interval.channel_data) != len(channel_headers):
                raise ValueError(
                    f"Mismatch between number of values ({len(interval.channel_data)}) "
                    f"and number of channels ({len(channel_headers)})"
                )

            row.extend(interval.channel_data)

            # Add status values if requested
            if include_statuses:
                status = interval.status
                status_values = [
                    getattr(status, field_name, None) for field_name in status_headers
                ]
                row.extend(status_values)

            writer.writerow(row)
