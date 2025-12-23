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
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, List

from emop_frame_protocol.emop_profile_log_1_record import EmopProfileLog1Record
from emop_frame_protocol.emop_profile_log_2_record import EmopProfileLog2Record

# mypy: disable-error-code="import-untyped"
from simt_emlite.mediator.mediator_client_exception import MediatorClientException
from simt_emlite.profile_logs.downloader_config import DownloaderConfig
from simt_emlite.profile_logs.profile_downloader import ProfileDownloader
from simt_emlite.profile_logs.replica_utils import check_missing_files_for_folder
from simt_emlite.smip.smip_csv import SMIPCSV
from simt_emlite.smip.smip_file_finder_result import SMIPFileFinderResult
from simt_emlite.smip.smip_reading_factory import create_smip_readings

USAGE_EXAMPLES = """
Examples:
  Single Day mode:
    python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21

  Config file mode:
    python -m simt_emlite.cli.profile_download --config config.downloader.properties
"""


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
) -> bool:
    """Download profile logs for a single day and write to CSV.

    Args:
        date: Date to download data for
        output_dir: Output directory for CSV files
        serial: Meter serial number (optional - one of serial or name)
        name: Meter name [meter_registry.name] (optional - one of serial or name)

    Return:
        success: download was successful
    """
    print(f"Starting profile download for serial {serial} on date {date}")

    try:
        downloader = ProfileDownloader(
            date=date,
            output_dir=output_dir,
            serial=serial,
            name=name,
        )

        # TODO: consider restoring the override logic which would cause download
        #       to go ahead even if file exists here:
        find_result: SMIPFileFinderResult = downloader.find_download_file()
        if find_result.found:
            print(
                f"skipping ... file already exists for serial [{downloader.serial}] [{find_result.smip_file}]"
            )
            return True

        log_1_records: Dict[datetime.datetime, EmopProfileLog1Record] = (
            downloader.download_profile_log_1_day()
        )
        log_2_records: Dict[datetime.datetime, EmopProfileLog2Record] = (
            downloader.download_profile_log_2_day()
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
            print(f"Wrote {len(readings_a)} readings to CSV in {output_dir}")

        if readings_b:
            SMIPCSV.write_from_smip_readings(
                serial=downloader.serial,
                output_dir=output_dir,
                readings=readings_b,
                element_marker="B",
            )
            print(f"Wrote {len(readings_b)} readings to CSV in {output_dir}")

        print(f"Profile download completed for {serial} on {date}")

        return True

    except NotImplementedError:
        # Three phase not supported - error already logged
        print("Caught NotImplementedError - three phase not supported")

    except MediatorClientException as e:
        if e.code_str == "DEADLINE_EXCEEDED":
            print(
                f"Meter timeout for serial=[{downloader.serial}], name=[{downloader.name}]"
            )
        else:
            print(
                f"MediatorClientException code=[{e.code_str}], message=[{e.message}] "
                f"for serial=[{downloader.serial}], name=[{downloader.name}]"
            )

    return False


def process_group(config: DownloaderConfig, group_name: str) -> None:
    """Process a single group from the configuration.

    Args:
        config: The downloader configuration instance
        group_name: Name of the group to process
    """
    groups = config.get_groups()
    group = groups[group_name]

    start_date = group.startdate
    end_date = group.enddate
    adjust_year = group.yearadjust is not None and group.yearadjust > 0
    adjust_years = group.yearadjust

    # When in testmode only run the groups that have the testmode property set
    if config.get_test_mode() and not group.test:
        print(f"Skipping {group_name}: test mode is enabled and group.test is not set")
        return

    print(f"Processing {group_name}: [ Retrieving from {start_date} to {end_date} ]")

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

    if not missing_dates:
        print(
            f"No missing files for {group_name} in date range {start_date} to {end_date}"
        )
        return

    print(f"Found {len(missing_dates)} missing dates for {group_name}")

    # Loop through only the missing dates (already sorted in ascending order)
    for current_date in missing_dates:
        success = False
        try:
            success = download_single_day(
                name=f"{config.get_esco().upper()}.{group.folder}",
                date=current_date,
                output_dir=output_dir,
                serial=None,
            )
        except Exception as e:
            print(f"Error processing {group_name} for date {current_date}: {e}")
            traceback.print_exc()
            # Continue with next date instead of stopping entirely

        if not success:
            break

    print(f"Completed processing group: {group_name}")


def run_config_mode(config_file: str) -> None:
    """Run the downloader in config mode, processing all groups from the config file.

    Groups are processed in parallel using a thread pool executor.

    Args:
        config_file: Path to the configuration file (e.g., config.downloader.properties)
    """
    config = DownloaderConfig.get_instance(config_file)

    print(f"rootfolder={config.get_root_folder()}")
    print(f"sleepseconds={config.get_sleep_seconds()}")
    print(f"testmode={config.get_test_mode()}")
    print(f"esco={config.get_esco()}")

    # Get groups
    groups = config.get_groups()
    group_names = list(groups.keys())
    print(f"Groups: {group_names}")

    # Process groups in parallel
    max_parallel_groups = 60
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_parallel_groups
    ) as executor:
        futures = [
            executor.submit(process_group, config, group_name)
            for group_name in group_names
        ]

        concurrent.futures.wait(futures)

        # Check for any exceptions that occurred in the futures
        for future in futures:
            try:
                future.result()  # This will raise any exception that occurred
            except Exception as e:
                print(f"Error in group processing: {e}")
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

    args = parser.parse_args()

    try:
        if args.config:
            # Config mode - process all groups from config file
            run_config_mode(args.config)
        elif args.serial and args.date:
            # Single day mode
            download_single_day(
                serial=args.serial, date=args.date, output_dir=args.output
            )
        else:
            print(USAGE_EXAMPLES)
            parser.error("Either --config or both --serial and --date are required")

        print("Profile download completed successfully")

    except Exception as e:
        print(
            f"Profile download failed: {e}, exception [{traceback.format_exception(e)}]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
