import argparse
import datetime
import importlib
import inspect
import json
import logging
import os
import sys
import traceback
from decimal import Decimal
from typing import Any, Dict, List, cast

import argcomplete
from emop_frame_protocol.emop_message import EmopMessage  # type: ignore[import-untyped]
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from simt_emlite.mediator.api_management import EmliteMeterManagementAPI
from simt_emlite.mediator.api_prepay import EmlitePrepayAPI
from simt_emlite.mediator.mediator_client_exception import MediatorClientException
from simt_emlite.mediator.validation import (
    cli_valid_decimal,
    cli_valid_event_log_idx,
    cli_valid_rate,
    cli_valid_switch,
)
from simt_emlite.util.config import load_config, set_config
from simt_emlite.util.logging import suppress_noisy_loggers

# Configure logging early to avoid being overridden by imports
logging.basicConfig(level=logging.WARNING)

console = Console(stderr=True)

config = load_config()

MEDIATOR_SERVER: str | None = cast(str | None, config["mediator_server"])

SIMPLE_READ_COMMANDS = {
    "backlight",
    "clock_time_read",
    "csq",
    "daylight_savings_correction_enabled",
    "firmware_version",
    "hardware",
    "instantaneous_active_power",
    "instantaneous_active_power_element_a",
    "instantaneous_active_power_element_b",
    "instantaneous_voltage",
    "load_switch",
    "prepay_balance",
    "prepay_enabled",
    "prepay_no_debt_recovery_when_emergency_credit_enabled",
    "prepay_no_standing_charge_when_power_fail_enabled",
    "prepay_transaction_count",
    "read",
    "read_element_a",
    "read_element_b",
    "serial_read",
    "tariffs_active_read",
    "tariffs_future_read",
    "tariffs_time_switches_element_a_or_single_read",
    "tariffs_time_switches_element_b_read",
    "three_phase_hardware_configuration",
    "three_phase_instantaneous_voltage",
    "three_phase_read",
    "three_phase_serial",
}


"""
    This is a CLI wrapper around the mediator client.
"""


def rich_status_circle(color: str) -> str:
    return f"[{color}]●[/{color}]"


def rich_signal_circle(csq: int | None) -> Text:
    if csq is None or csq < 1:
        color = "rgb(255,0,0)"  # Red
    elif csq > 22:
        color = "rgb(0,255,0)"  # Green
    elif csq > 17:
        color = "rgb(128,255,0)"  # Light Green
    elif csq > 12:
        color = "rgb(255,255,0)"  # Yellow
    elif csq > 7:
        color = "rgb(255,192,0)"  # Orange-yellow
    elif csq > 0:
        color = "rgb(255,128,0)"  # Orange
    return Text("●", style=color)


class EMOPCLI(EmlitePrepayAPI, EmliteMeterManagementAPI):
    def __init__(
        self,
        serial: str | None = None,
        emnify_id: str | None = None,
        logging_level: str | int = logging.INFO,
    ) -> None:
        self.serial = serial
        self.supabase = None

        try:
            # TODO: necessary for meters that have not yet had a serial read
            #       they will be in the registry but with a NULL serial
            if emnify_id is not None:
                err_msg = "emnify_id lookup is not yet supported."
                console.print(err_msg)
                raise Exception(err_msg)

            # Initialize client (without meter_id, but with resolved address)
            super().__init__(
                mediator_address=MEDIATOR_SERVER,
                logging_level=logging_level,
            )
        except Exception as e:
            console.print(
                f"Failure: [{e}], exception [{traceback.format_exception(e)}]"
            )
            # Re-raise unless it's just a missing serial for commands that don't need it?
            # Existing emop.py re-raises.
            raise e

    # =================================
    #   Info Commands
    # =================================

    def info(self, serial: str) -> None:
        """Call the new InfoService GetInfo via the client."""
        if not serial:
            raise ValueError("Serial required for info command")

        # Use the meter_info method inherited from EmliteMeterManagementAPI
        # which calls the gRPC service
        info_json = self.meter_info(serial)
        # Parse it just to pretty print it
        try:
            data = json.loads(info_json)
            print(json.dumps(data, indent=2))
        except Exception:
            print(info_json)

    def clock_drift(self, serial: str) -> None:
        """Get clock drift information for a specific meter."""
        if not serial:
            raise ValueError("Serial required for clock_drift command")

        # Use the meter_clock_drift method inherited from EmliteMeterManagementAPI
        result = self.meter_clock_drift(serial)
        print(json.dumps(result, indent=2))

    def list(self, json_output: bool = False, esco: str | None = None) -> None:
        """List all meters with formatted table output."""
        # Call inherited meter_list() method
        meters_json = self.meter_list(esco=esco)


        # Parse the JSON response
        try:
            meters = json.loads(meters_json)
        except Exception as e:
            console.print(f"Failed to parse meters data: {e}")
            raise

        # Sort meters by name
        meters.sort(key=lambda x: x.get("name") or "")

        # JSON output for scripting
        if json_output:
            print(json.dumps(meters, indent=2))
            return

        # Rich table output for human readability
        table = Table(
            "esco",
            "serial",
            "name",
            "signal",
            "health",
            "hardware",
            "feeder",
            box=box.SQUARE,
        )

        for meter in meters:
            row_values = [
                meter.get("esco", ""),
                meter.get("serial", ""),
                meter.get("name", ""),
                rich_signal_circle(meter.get("csq")),
                rich_status_circle("green" if meter.get("health") == "healthy" else "red"),
                meter.get("hardware", ""),
                meter.get("feeder", ""),
            ]
            table.add_row(*row_values)

        console.print(table)

    # =================================
    #   Tool related
    # =================================

    def version(self) -> None:
        version = importlib.metadata.version("simt-emlite")
        print(version)

    def env_show(self) -> None:
        print(config["env"])

    def env_set(self, env: str) -> None:
        try:
            set_config(env)
            print(f"env set to {env}")
        except Exception as e:
            logging.error(f"ERROR: {e}")
            sys.exit(1)


def valid_log_level(level_str: str | None) -> Any:
    if level_str is None:
        raise argparse.ArgumentTypeError("log level cannot be None")
    try:
        return getattr(logging, level_str.upper())
    except AttributeError:
        raise argparse.ArgumentTypeError(f"Invalid log level: {level_str}")


def valid_iso_datetime(timestamp: str | None) -> datetime.datetime:
    if timestamp is None:
        raise argparse.ArgumentTypeError("event log idx cannot be None")
    try:
        dt = datetime.datetime.fromisoformat(timestamp)
        # Ensure timezone-aware datetime for epoch conversion
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid ISO datetime format: {timestamp}")


# Use validation from shared module
valid_event_log_idx = cli_valid_event_log_idx


# Use validation from shared module
valid_decimal = cli_valid_decimal


# Use validation from shared module
valid_rate = cli_valid_rate


# Use validation from shared module
valid_switch = cli_valid_switch


def valid_backlight_setting(setting: str) -> EmopMessage.BacklightSettingType:
    if setting == "normal_sp" or setting == "always_off_3p":
        return EmopMessage.BacklightSettingType.normal_sp_or_always_off_3p
    elif setting == "always_on_sp":
        return EmopMessage.BacklightSettingType.always_on_sp
    elif setting == "always_off_sp":
        return EmopMessage.BacklightSettingType.always_off_sp
    elif setting == "always_on_3p":
        return EmopMessage.BacklightSettingType.always_on_3p
    elif setting == "always_off_3p":
        return EmopMessage.BacklightSettingType.always_off_3p
    elif setting == "30_seconds_turn_off_3p":
        return EmopMessage.BacklightSettingType.n30_seconds_turn_off_3p
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid or unsupported backlight setting string '{setting}'. See choices with -h."
        )


def valid_load_switch_setting(setting: str) -> EmopMessage.LoadSwitchSettingType:
    if setting == "never_button_required":
        return EmopMessage.LoadSwitchSettingType.never_button_required
    elif setting == "normal_button_always":
        return EmopMessage.LoadSwitchSettingType.normal_button_always
    elif setting == "no_button_prepay_mode":
        return EmopMessage.LoadSwitchSettingType.no_button_prepay_mode
    elif setting == "no_button_credit_mode":
        return EmopMessage.LoadSwitchSettingType.no_button_credit_mode
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid or unsupported load switch setting string '{setting}'. See choices with -h."
        )


def add_arg_serial(parser: argparse.ArgumentParser) -> None:
    """Adds optional positional argument serial"""
    parser.add_argument("serial", help="meter serial", nargs="?")


def args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
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

    parser.add_argument("-s", help="Serial", required=False)
    parser.add_argument(
        "--serials",
        help="Run command for all serials in given comma delimited list",
        required=False,
    )
    parser.add_argument(
        "--serials-file",
        help="Run command for all serials in given file that has a serial per line.",
        required=False,
    )

    subparsers = parser.add_subparsers(dest="subparser")

    # Helper functions for argument setup
    def setup_no_args(p: argparse.ArgumentParser) -> None:
        pass

    def setup_serial(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)

    def setup_env_set(p: argparse.ArgumentParser) -> None:
        p.add_argument("env")

    def setup_list(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--json",
            help="Output as JSON instead of formatted table",
            action="store_true",
            dest="json_output",
        )
        p.add_argument(
            "--esco",
            help="Filter by ESCO code (e.g. wlce)",
            required=False,
        )

    def setup_event_log(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "log_idx",
            type=valid_event_log_idx,
            help="value 0-9 where 0 returns the latest 10 log entries; 9 the oldest 10 entries",
        )

    def setup_profile_log(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "--timestamp",
            help="Timestamp in iso8601 format (eg. 2024-08-21 or 2024-08-21T14:00) of time to read profile logs for.",
            required=True,
            type=valid_iso_datetime,
        )

    def setup_three_phase_intervals(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "--day",
            help="Date to pull intervals for.",
            required=False,
            type=valid_iso_datetime,
        )
        p.add_argument(
            "--start-time",
            help="Start date time for intervals range.",
            required=False,
            type=valid_iso_datetime,
        )
        p.add_argument(
            "--end-time",
            help="End date time for intervals range.",
            required=False,
            type=valid_iso_datetime,
        )
        p.add_argument(
            "--csv",
            help="Path to CSV file to output intervals data",
            required=True,
            type=str,
        )
        p.add_argument(
            "--include_statuses",
            help="Include statuses in the CSV",
            required=False,
            action="store_true",
        )

    def setup_obis_read(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument("obis", help="obis / objectid to read")

    def setup_obis_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument("obis", help="obis / objectid to read")
        p.add_argument("payload_hex", help="payload to write to obis (hex string)")

    def setup_prepay_enabled_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "enabled",
            type=valid_switch,
            help="set prepay flag (on=prepay mode, off=credit mode)",
        )

    def setup_daylight_savings_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "enabled",
            type=valid_switch,
            help="set daylight_savings_correction flag (on, off)",
        )

    def setup_prepay_send_token(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument("token", help="prepay token obtained from topupmeters.co.uk")

    def setup_backlight_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "setting",
            help="new backlight setting",
            type=valid_backlight_setting,
        )

    def setup_load_switch_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "setting",
            help="new load_switch setting",
            type=valid_load_switch_setting,
        )

    def setup_tariffs_future_write(p: argparse.ArgumentParser) -> None:
        add_arg_serial(p)
        p.add_argument(
            "--from-ts",
            help="Date and time in iso8601 format of when the date tariff will apply from. NOTE: this is a clock time meaning in summer the BST time should be used here. If however a meter was configured with the daylight savings flag UNCHECKED then it should be UTC.",
            required=True,
            type=valid_iso_datetime,
        )
        p.add_argument(
            "--unit-rate",
            help="Tariff unit rate (eg. '0.25' is 25 pence)",
            required=True,
            type=valid_rate,
        )
        p.add_argument(
            "--standing-charge",
            help="Tariff standing charge (eg. '0.695' is 69.5 pence)",
            required=True,
            type=valid_rate,
        )
        p.add_argument(
            "--emergency-credit",
            help="Emergency credit level (eg. '15.00' is 15 GBP)",
            required=False,
            default=Decimal("15.00"),
            type=valid_decimal,
        )
        p.add_argument(
            "--ecredit-availability",
            help="Emergency credit availability level. EC button can be pressed when balance goes under this. (eg. '10.00' is 10 GBP)",
            required=False,
            default=Decimal("10.00"),
            type=valid_decimal,
        )
        p.add_argument(
            "--debt-recovery-rate",
            help="Daily rate of debt recovery (eg. '0.3' is 30 pence)",
            required=False,
            default=Decimal("0.30"),
            type=valid_decimal,
        )

    # Command Definitions
    # (command_name, help_text, setup_func, description)
    # Commands are grouped by API module and alphabetized within groups.

    # 1. Management / Tooling
    management_commands = [
        ("clock_drift", "Show clock time drift for a meter", setup_serial, None),
        ("env_set", "Set CLI environment context [points ~/.simt/emlite.env at ~/.simt/emlite.<env>.env]", setup_env_set, None),
        ("env_show", "Show current environment context", setup_no_args, None),
        ("info", "metadata and shadows data for a meter", setup_serial, None),
        ("list", "List all meters with status", setup_list, None),
        ("serial_to_name", "lookup meter name from serial", setup_serial, None),
        ("version", "Show version", setup_no_args, None),
    ]

    # 2. Core API
    core_commands = [
        ("backlight", "Backlight setting", setup_serial, None),
        ("backlight_write", "Write backlight setting to meter", setup_backlight_write, """Supported settings:

  Single Phase Meters:

    normal_sp = off until button pressed on meter
    always_on_sp = light always on (lcd burnout!)
    always_off_sp = light never on

  Three Phase Meters:

    30_seconds_turn_off_3p = turn off after 30 seconds
    always_on_3p = light always on (lcd burnout!)
    always_off_3p = light never on

Example usage:

emop -s EML1411222333 backlight_write normal_sp
"""),
        ("clock_time_read", "Current clock time on the meter", setup_serial, None),
        ("clock_time_write", "Update clock time with current timestamp", setup_serial, None),
        ("csq", "Signal quality", setup_serial, None),
        ("daylight_savings_correction_enabled", "Is daylight savings correction enabled?", setup_serial, None),
        ("daylight_savings_correction_enabled_write", "Set daylight_savings_correction flag", setup_daylight_savings_write, None),
        ("event_log", "Read a block of 10 events from the event log at a given index", setup_event_log, """Read a block of 10 events from the event log at the given index.

The log_idx argument (0-9) determines which block of 10 events to read:
  0 = most recent 10 events
  9 = oldest 10 events

Example usage:

  emop -s EML1411222333 event_log 0
"""),
        ("firmware_version", "Firmware version code", setup_serial, None),
        ("hardware", "Hardware code", setup_serial, None),
        ("instantaneous_active_power", "Current active power (single or combined)", setup_serial, None),
        ("instantaneous_active_power_element_a", "Current active power (element a)", setup_serial, None),
        ("instantaneous_active_power_element_b", "Current active power (element b)", setup_serial, None),
        ("instantaneous_voltage", "Current voltage", setup_serial, None),
        ("load_switch", "Load switch setting", setup_serial, None),
        ("load_switch_write", "Write load_switch setting to meter", setup_load_switch_write, """Supported settings:
    normal_button_always
    no_button_prepay_mode
    no_button_credit_mode
    never_button_required

Example usage:

emop -s EML1411222333 load_switch_write never_button_required
"""),
        ("obis_read", "read a payload from an arbitrary obis / object id", setup_obis_read, """Read raw data from an arbitrary OBIS code / object id.

The obis argument should be an OBIS triplet (e.g. "1.0.0") or object id.

Example usage:

  emop -s EML1411222333 obis_read 1.0.0
"""),
        ("obis_write", "Write a payload to an arbitrary obis / object id", setup_obis_write, """Write raw data to an arbitrary OBIS code / object id.

Arguments:
  obis        - OBIS triplet (e.g. "1.0.0") or object id
  payload_hex - hex string of the payload to write

Example usage:

  emop -s EML1411222333 obis_write 1.0.0 01020304
"""),
        ("profile_log_1", "Fetch half hourly profile log 1 data for a given date time.", setup_profile_log, """Fetch half hourly data for a given date time.

Example usage:

  emop -s EML1411222333 profile_log_1 --timestamp 2024-08-21T14:00
"""),
        ("profile_log_2", "Fetch half hourly profile log 2 data for a given date time.", setup_profile_log, """Fetch half hourly data for a given date time.

Example usage:

  emop -s EML1411222333 profile_log_2 --timestamp 2024-08-21T14:00
"""),
        ("read", "Current read - will read all available for meter type", setup_serial, None),
        ("read_element_a", "Current read on element A", setup_serial, None),
        ("read_element_b", "Current read on element B", setup_serial, None),
        ("serial_read", "Meter serial", setup_serial, None),
        ("three_phase_hardware_configuration", "Three phase hardware configuration", setup_serial, None),
        ("three_phase_instantaneous_voltage", "Current three phase voltage (if three phase meter)", setup_serial, None),
        ("three_phase_intervals", "Fetch three phase intervals for given time range.", setup_three_phase_intervals, """Fetch three phase intervals for given time range.

Example usage:

emop -s EML1411222333 three_phase_intervals --start-time "2025-02-20T00:00+00" --end-time "2025-02-21T00:00+00"
"""),
        ("three_phase_read", "Three phase reading", setup_serial, None),
        ("three_phase_serial", "Three phase meter serial", setup_serial, None),
    ]

    # 3. Prepay API
    prepay_commands = [
        ("prepay_balance", "Current prepay balance (if in prepay mode)", setup_serial, None),
        ("prepay_enabled", "Is prepay mode enabled?", setup_serial, None),
        ("prepay_enabled_write", "Set prepay mode flag", setup_prepay_enabled_write, None),
        ("prepay_no_debt_recovery_when_emergency_credit_enabled", "Is no debt recovery in ecredit mode enabled?", setup_serial, None),
        ("prepay_no_standing_charge_when_power_fail_enabled", "Is no standing charge when power fail enabled?", setup_serial, None),
        ("prepay_send_token", "Write a prepay token to the meter to topup the balance", setup_prepay_send_token, None),
        ("prepay_transaction_count", "Count of prepay transactions (0 indexed so is num tx - 1)", setup_serial, None),
        ("tariffs_active_read", "Current tariff settings", setup_serial, None),
        ("tariffs_future_read", "Future tariff settings", setup_serial, None),
        ("tariffs_future_write", "Write future tariffs to meter", setup_tariffs_future_write, """Write future dated tariffs and emergency credit properties into the meter.

Example usage:

emop -s EML1411222333 tariffs_future_write \\
        --from-ts "2024-08-21T06:54:00+00" \\
        --unit-rate "0.23812" \\
        --standing-charge "0.6975" \\
        --ecredit-availability "10.0" \\
        --debt-recovery-rate "0.25" \\
        --emergency-credit "15.00"
"""),
        ("tariffs_time_switches_element_a_or_single_read", "Time switches for element A", setup_serial, None),
        ("tariffs_time_switches_element_b_read", "Time switches for element B", setup_serial, None),
    ]

    # Define command groups for help display
    command_groups = [
        ("Management", management_commands),
        ("Core (Meter Reads/Writes)", core_commands),
        ("Prepay & Tariffs", prepay_commands),
    ]

    # Add all groups to subparsers
    all_commands = management_commands + core_commands + prepay_commands

    for cmd, help_text, setup_func, description in all_commands:
        p = subparsers.add_parser(
            cmd,
            help=help_text,
            description=description or help_text,
            formatter_class=argparse.RawDescriptionHelpFormatter if description else argparse.HelpFormatter,
        )
        setup_func(p)

    # Store command groups on parser for custom help
    parser._command_groups = command_groups  # type: ignore[attr-defined]

    return parser


def run_command(serial: str | None, command: str, kwargs: Dict[str, Any]) -> None:
    log_level = kwargs.pop("log_level", None)

    verbose = kwargs.pop("verbose", False)
    if verbose is True:
        log_level = logging.DEBUG

    try:
        with console.status(f"[bold green]Running {command}...", spinner="dots"):
            cli = EMOPCLI(serial=serial, logging_level=log_level)
            method = getattr(cli, command)

            # INSPECT: Check if the method expects a 'serial' argument as the first parameter
            # EMOPCLI methods inherited from EmliteMediatorAPI mostly start with (self, serial, ...)
            # except those that don't need it.
            # Local methods like 'info' use 'self.serial' internally and don't take it as arg.
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            if params and params[0] == "serial":
                if serial is None:
                    raise ValueError(f"Command '{command}' requires a serial number")
                result = method(serial, **kwargs)
            else:
                result = method(**kwargs)

        if result is not None:
            if command == "three_phase_intervals":
                return

            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, default=str))
            elif isinstance(result, (int, float, str, Decimal)):
                if command in SIMPLE_READ_COMMANDS:
                    print(f"{command}={result}")
                else:
                    print(result)
            else:
                print(result)
    except MediatorClientException as e:
        if e.code_str == "EMLITE_CONNECTION_FAILURE":
            logging.error("Failed to connect to meter")
        else:
            logging.error(f"Failure [{e}]")
    except Exception as e:
        # assume constructor or method already handled logging but just in case
        # print wrapper trace if needed or rely on higher level
        # console.print(f"Error executing command: {e}")
        raise e


def run_command_for_serials(
    serial_list: List[str], command: str, kwargs: Dict[str, Any]
) -> None:
    for serial in serial_list:
        console.print(f"\nrunning '{command}' for meter {serial} ...\n")
        run_command(serial, command, kwargs.copy())


def print_grouped_help(parser: argparse.ArgumentParser) -> None:
    """Print help with commands grouped by category."""
    print("usage: emop [-h] [--log-level LOG_LEVEL] [--verbose] [-s S]")
    print("            [--serials SERIALS] [--serials-file SERIALS_FILE] command ...")
    print()

    if hasattr(parser, "_command_groups"):
        print("commands:")
        for group_name, commands in parser._command_groups:  # type: ignore[attr-defined]
            print(f"\n  {group_name}:")
            for cmd, help_text, _, _ in commands:
                # Truncate help text if too long
                if len(help_text) > 50:
                    help_text = help_text[:47] + "..."
                print(f"    {cmd:42} {help_text}")
        print()

    print("options:")
    print("  -h, --help            show this help message and exit")
    print("  --log-level LOG_LEVEL")
    print("                        Set logging level [debug, info, warning (default), warn, error, critical]")
    print("  --verbose             Alias for '--log-level debug'")
    print("  -s S                  Serial")
    print("  --serials SERIALS     Run command for all serials in given comma delimited list")
    print("  --serials-file SERIALS_FILE")
    print("                        Run command for all serials in given file that has a serial per line.")


def main() -> None:
    # supress supabase py request logging and underlying noisy libs:
    suppress_noisy_loggers()

    parser = args_parser()

    # support autocompletion - see https://kislyuk.github.io/argcomplete
    argcomplete.autocomplete(parser)

    kwargs = vars(parser.parse_args())

    # Handle help flag ourselves for grouped output
    if kwargs.pop("help", False):
        print_grouped_help(parser)
        exit(0)

    command = kwargs.pop("subparser")
    if command is None:
        print_grouped_help(parser)
        exit(-1)

    # CLI works on a given serial or list of serials.
    arg_s = kwargs.pop("s", None)
    arg_serial = kwargs.pop("serial", None)
    arg_serials = kwargs.pop("serials", None)
    arg_serials_file = kwargs.pop("serials_file", None)

    serial = arg_s or arg_serial
    try:
        # Commands that don't need a serial or can work without one
        if command in ["env_set", "env_show", "version", "list"]:
            run_command(serial, command, kwargs)
        elif serial:
            run_command(serial, command, kwargs)
        elif arg_serials:
            serial_list = arg_serials.split(",")
            run_command_for_serials(serial_list, command, kwargs)
        elif arg_serials_file:
            if not os.path.exists(arg_serials_file):
                logging.error(f"ERROR: serials file {arg_serials_file} does not exist")
                sys.exit(2)

            with open(arg_serials_file, "r") as f:
                serial_list = [line.strip() for line in f]

            run_command_for_serials(serial_list, command, kwargs)
        else:
            # check commands that might be self-contained in methods/args?
            # info requires serial in V2
            parser.print_help()
            exit(-1)
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]KeyboardInterrupt: Operation cancelled by user.[/yellow]"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
