#!/usr/bin/env python3
"""
Profile Download Script

This script provides profile log downloading functionality with two modes:
1. Single day mode: Download for a specific serial and date
2. Config mode: Process multiple groups from a configuration file

Usage:
    Single day mode:
        python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21

    Config mode:
        python -m simt_emlite.cli.profile_download --config config.downloader.properties
"""

import argparse
import concurrent.futures
import datetime
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record
from rich.console import Console

# mypy: disable-error-code="import-untyped"
from simt_emlite.mediator.mediator_client_exception import MediatorClientException
from simt_emlite.profile_logs.downloader_config import DownloaderConfig
from simt_emlite.profile_logs.profile_downloader import ProfileDownloader
from simt_emlite.profile_logs.replica_utils import check_missing_files_for_folder
from simt_emlite.smip.smip_csv import SMIPCSV
from simt_emlite.smip.smip_file_finder_result import SMIPFileFinderResult
from simt_emlite.smip.smip_reading_factory import create_smip_readings
from simt_emlite.util.logging import suppress_noisy_loggers

# Configure logging early
logging.basicConfig(level=logging.WARNING)

console = Console(stderr=True)

USAGE_EXAMPLES = """
Examples:
  Single Day mode:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21

  Config file mode:
    python -m simt_emlite.cli.profile_download --config config.downloader.properties

  With debug logging:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21 --log-level debug
"""


def valid_log_level(level_str: str | None) -> Any:
    if level_str is None:
        raise argparse.ArgumentTypeError("log level cannot be None")
    try:
        return getattr(logging, level_str.upper())
    except AttributeError:
        raise argparse.ArgumentTypeError(f"Invalid log level: {level_str}")


def valid_date(date_str: str) -> datetime.date:
    """Validate and parse date string in YYYY-MM-DD format"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def download_single_day(
    date: datetime.date,
    output_dir: str,
    serial: str | None = None,
    name: str | None = None,
    status: Any = None,
    logging_level: int = logging.WARNING,
    use_spinner: bool = True,
) -> Tuple[bool, Optional[datetime.date]]:
    """Download profile logs for a single day and write to CSV.

    Args:
        date: Date to download data for
        output_dir: Output directory for CSV files
        serial: Meter serial number (optional - one of serial or name)
        name: Meter name [meter_registry.name] (optional - one of serial or name)
        status: Rich status object for updating the spinner message

    Return:
        success: download was successful
    """
    from contextlib import nullcontext

    status_context: Any
    if use_spinner:
        if status is None:
            status_context = console.status(
                f"[bold green]Downloading {serial or name} for {date}...",
                spinner="dots",
            )
        else:
            # Use existing status object
            status_context = nullcontext()
            status.update(
                f"[bold green]Downloading {serial or name} for {date}...",
                spinner="dots",
            )
    else:
        status_context = nullcontext()

    downloader: ProfileDownloader

    with status_context as s:
        # If we created a new status context, 's' is the status object
        active_status = s if s else status

        def update_progress(msg: str):
            if active_status:
                active_status.update(
                    f"[bold green]Downloading {serial or name} for {date} - {msg}..."
                )

        try:
            downloader = ProfileDownloader(
                date=date,
                output_dir=output_dir,
                serial=serial,
                name=name,
                logging_level=logging_level,
            )

            # TODO: consider restoring the override logic which would cause download
            #       to go ahead even if file exists here:
            find_result: SMIPFileFinderResult = downloader.find_download_file()
            if find_result.found:
                console.print(
                    f"skipping ... file already exists for serial [{downloader.serial}] [{find_result.smip_file}]"
                )
                return True, None

            log_1_records: Dict[datetime.datetime, EmopProfileLog1Record] = (
                downloader.download_profile_log_1_day(progress_callback=update_progress)
            )
            log_2_records: Dict[datetime.datetime, EmopProfileLog2Record] = (
                downloader.download_profile_log_2_day(progress_callback=update_progress)
            )

            # Create start and end datetime for the day (timezone-aware)
            start_time = datetime.datetime.combine(date, datetime.time.min).replace(
                tzinfo=datetime.timezone.utc
            )
            end_time = datetime.datetime.combine(date, datetime.time.max).replace(
                tzinfo=datetime.timezone.utc
            )

            assert downloader.serial is not None

            # Create SMIP readings from the downloaded profile logs
            readings_a, readings_b = create_smip_readings(
                serial=downloader.serial,
                start_time=start_time,
                end_time=end_time,
                log1_records=log_1_records,
                log2_records=log_2_records,
                is_twin_element=downloader.is_twin_element,
            )

            # Write readings to CSV
            if readings_a:
                SMIPCSV.write_from_smip_readings(
                    serial=downloader.serial,
                    output_dir=output_dir,
                    readings=readings_a,
                    element_marker="A" if downloader.is_twin_element else None,
                )
                console.print(
                    f"Wrote {len(readings_a)} A readings to CSV in {output_dir} for date {downloader.date}"
                )

            if readings_b:
                SMIPCSV.write_from_smip_readings(
                    serial=downloader.serial,
                    output_dir=output_dir,
                    readings=readings_b,
                    element_marker="B",
                )
                console.print(
                    f"Wrote {len(readings_b)} B readings to CSV in {output_dir} for date {downloader.date}"
                )

            identifier = (
                downloader.name
                if downloader and downloader.name is not None
                else serial
            )
            console.print(f"Profile download completed for {identifier} on {date}")

            return True, downloader.future_date_detected

        except NotImplementedError:
            # Three phase not supported - error already logged
            console.print("Caught NotImplementedError - three phase not supported")

        except MediatorClientException as e:
            if e.code_str == "DEADLINE_EXCEEDED":
                console.print(
                    f"Meter timeout for serial=[{downloader.serial}], name=[{downloader.name}], date=[{downloader.date}]"
                )
            else:
                console.print(
                    f"MediatorClientException code=[{e.code_str}], message=[{e.message}] "
                    f"for serial=[{downloader.serial}], name=[{downloader.name}], date=[{downloader.date}]"
                )

        return False, None


def gather_missing_dates_for_group(
    config: DownloaderConfig, group_name: str
) -> Tuple[str, List[datetime.date]]:
    """Check for missing files for a single group.

    Args:
        config: The downloader configuration instance
        group_name: Name of the group to process

    Returns:
        Tuple of (group_name, list of missing dates)
    """
    groups = config.get_groups()
    group = groups[group_name]

    start_date = group.startdate
    end_date = group.enddate
    adjust_year = group.yearadjust is not None and group.yearadjust > 0
    adjust_years = group.yearadjust

    # When in testmode only run the groups that have the testmode property set
    if config.get_test_mode() and not group.test:
        return group_name, []

    # Build the output path by joining rootfolder with the group's folder
    root_folder = config.get_root_folder()
    if group.folder:
        output_dir = os.path.join(str(root_folder), str(group.folder))
    else:
        output_dir = str(root_folder)

    # Apply year adjustment if configured
    if adjust_year and adjust_years:
        start_date = start_date.replace(year=start_date.year + adjust_years)
        end_date = end_date.replace(year=end_date.year + adjust_years)

    # Find only the dates that are missing files
    missing_dates: List[datetime.date] = check_missing_files_for_folder(
        folder_path=Path(output_dir),
        start_date=start_date,
        end_date=end_date,
    )
    return group_name, missing_dates


def print_missing_dates_json(missing_dates_by_group: Dict[str, List[datetime.date]]):
    """Print missing dates summary in JSON format."""
    # Convert dates to strings for JSON serialization
    json_output = {
        group: [d.isoformat() for d in dates]
        for group, dates in missing_dates_by_group.items()
    }
    print(json.dumps(json_output, indent=2))


def print_missing_dates_summary(missing_dates_by_group: Dict[str, List[datetime.date]]):
    """Print human-readable missing dates summary."""
    from rich.table import Table

    table = Table(title="Missing Dates Summary")
    table.add_column("Group", style="cyan")
    table.add_column("Missing Count", style="magenta")
    table.add_column("Date Range / Dates", style="green")

    total_missing = 0
    for group, dates in sorted(missing_dates_by_group.items()):
        count = len(dates)
        total_missing += count
        if count > 0:
            if count > 5:
                dates_str = f"{dates[0]} ... {dates[-1]}"
            else:
                dates_str = ", ".join(str(d) for d in dates)
            table.add_row(group, str(count), dates_str)

    console.print(table)
    console.print(
        f"[bold]Total missing files across all groups: {total_missing}[/bold]"
    )


def process_group(
    config: DownloaderConfig,
    group_name: str,
    dates_to_process: List[datetime.date],
    logging_level: int = logging.WARNING,
) -> None:
    """Process a single group for specific dates.

    Args:
        config: The downloader configuration instance
        group_name: Name of the group to process
        dates_to_process: List of dates to download
        logging_level: Logging level
    """
    groups = config.get_groups()
    group = groups[group_name]

    if not dates_to_process:
        return

    console.print(
        f"Processing {group_name}: [ Downloading {len(dates_to_process)} days ]"
    )

    # Build the output path by joining rootfolder with the group's folder
    root_folder = config.get_root_folder()
    if group.folder:
        output_dir = os.path.join(str(root_folder), str(group.folder))
    else:
        output_dir = str(root_folder)

    # Loop through only the missing dates (already sorted in ascending order)
    skip_until_date: Optional[datetime.date] = None
    for current_date in dates_to_process:
        if skip_until_date and current_date < skip_until_date:
            continue

        success = False
        future_date: Optional[datetime.date] = None
        try:
            success, future_date = download_single_day(
                name=f"{config.get_esco().upper()}.{group.folder}",
                date=current_date,
                output_dir=output_dir,
                serial=None,
                logging_level=logging_level,
                use_spinner=False,
            )
            if success and future_date:
                skip_until_date = future_date
                console.print(
                    f"Future date detected: {future_date}. Skipping dates until then for group {group_name}"
                )

        except Exception as e:
            console.print(f"Error processing {group_name} for date {current_date}: {e}")
            traceback.print_exc()
            # Continue with next date instead of stopping entirely

        if not success:
            break

    console.print(f"Completed processing group (success={success}): {group_name}")


def run_config_mode(config_file: str, logging_level: int = logging.WARNING) -> None:
    """Run the downloader in config mode, processing all groups from the config file.

    1. Gather missing dates for all groups in parallel.
    2. Report missing dates.
    3. Process missing dates in parallel.

    Args:
        config_file: Path to the configuration file (e.g., config.downloader.properties)
    """
    config = DownloaderConfig.get_instance(config_file)

    console.print(f"rootfolder={config.get_root_folder()}")
    console.print(f"sleepseconds={config.get_sleep_seconds()}")
    console.print(f"testmode={config.get_test_mode()}")
    console.print(f"esco={config.get_esco()}")

    # Get groups
    groups = config.get_groups()
    group_names = list(groups.keys())
    console.print(f"Groups: {group_names}")

    # Step 1: Gather missing dates in parallel
    console.print("[bold yellow]Checking for missing files...[/bold yellow]")
    missing_dates_by_group: Dict[str, List[datetime.date]] = {}

    max_parallel_checks = 60
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_parallel_checks
    ) as executor:
        futures = {
            executor.submit(gather_missing_dates_for_group, config, name): name
            for name in group_names
        }

        for check_missing_future in concurrent.futures.as_completed(futures):
            try:
                g_name, missing = check_missing_future.result()
                if missing:
                    missing_dates_by_group[g_name] = missing
            except Exception as e:
                console.print(
                    f"[red]Error checking missing files for group {futures[check_missing_future]}: {e}[/red]"
                )
                traceback.print_exc()

    # Step 2: Write/Print summary
    if sys.stdout.isatty():
        print_missing_dates_summary(missing_dates_by_group)
    else:
        print_missing_dates_json(missing_dates_by_group)

    if not missing_dates_by_group:
        console.print("[green]No missing files found. All up to date.[/green]")
        return

    # Step 3: Process groups in parallel
    console.print("[bold yellow]Starting downloads...[/bold yellow]")
    max_parallel_downloads = 60
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_parallel_downloads
    ) as executor:
        futures_download = [
            executor.submit(process_group, config, group_name, dates, logging_level)
            for group_name, dates in missing_dates_by_group.items()
        ]

        concurrent.futures.wait(futures_download)

        # Check for any exceptions that occurred in the futures
        for download_future in futures_download:
            try:
                download_future.result()  # This will raise any exception that occurred
            except Exception as e:
                console.print(f"Error in group processing: {e}")
                traceback.print_exc()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile Download Script - Downloads profile log data",
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Config mode
    parser.add_argument(
        "--config",
        "-c",
        help="Configuration file for batch processing (e.g., config.downloader.properties)",
        type=str,
    )

    # Single day mode arguments
    parser.add_argument(
        "--serial",
        "-s",
        help="Meter serial number (required for single day mode)",
        type=str,
    )

    parser.add_argument(
        "--date",
        "-d",
        help="Date to download data for (YYYY-MM-DD format, required for single day mode)",
        type=valid_date,
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for CSV files (default: output). Must be a directory path, not a file path.",
        default="output",
        type=str,
    )

    # Logging arguments
    parser.add_argument(
        "--log-level",
        help="Set logging level [debug, info, warning (default), warn, error, critical]",
        default=logging.WARNING,
        required=False,
        type=valid_log_level,
    )

    parser.add_argument(
        "--verbose",
        help="Alias for '--log-level debug'",
        required=False,
        action="store_true",
    )

    args = parser.parse_args()

    # Set logging level
    log_level = args.log_level
    if args.verbose:
        log_level = logging.DEBUG

    logging.getLogger().setLevel(log_level)
    # suppress supabase py request logging and underlying noisy libs:
    suppress_noisy_loggers()

    try:
        if args.config:
            # Config mode - process all groups from config file
            run_config_mode(args.config, logging_level=log_level)
        elif args.serial and args.date:
            # Single day mode
            download_single_day(
                serial=args.serial,
                date=args.date,
                output_dir=args.output,
                logging_level=log_level,
            )
        else:
            console.print(USAGE_EXAMPLES)
            parser.error("Either --config or both --serial and --date are required")

        console.print("Profile download completed successfully")

    except KeyboardInterrupt:
        console.print(
            "\n[yellow]KeyboardInterrupt: Operation cancelled by user.[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(
            f"Profile download failed: {e}, exception [{traceback.format_exception(e)}]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
