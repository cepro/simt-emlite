import argparse
import datetime
import importlib
import json
import logging
import os
import sys
import traceback
import inspect
from decimal import Decimal
from typing import Any, Dict, List, cast

import argcomplete
from emop_frame_protocol.emop_message import EmopMessage  # type: ignore[import-untyped]
from rich.console import Console

from simt_emlite.mediator.client2 import EmliteMediatorClientV2
from simt_emlite.mediator.mediator_client_exception import MediatorClientException
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config, set_config
from simt_emlite.util.logging import suppress_noisy_loggers
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

# Configure logging early to avoid being overridden by imports
logging.basicConfig(level=logging.WARNING)

console = Console(stderr=True)

config = load_config()

SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
SUPABASE_ANON_KEY = config["supabase_anon_key"]
SUPABASE_URL = config["supabase_url"]

FLY_API_TOKEN = config["fly_api_token"]
FLY_REGION: str | None = cast(str | None, config["fly_region"])

ENV: str | None = cast(str | None, config["env"])

SIMPLE_READ_COMMANDS = [
    ("csq", "Signal quality"),
    ("hardware", "Hardware code"),
    ("firmware_version", "Firmware version code"),
    ("serial_read", "Meter serial"),
    ("clock_time_read", "Current clock time on the meter"),
    ("instantaneous_voltage", "Current voltage"),
    ("instantaneous_active_power", "Current active power (single or combined)"),
    ("instantaneous_active_power_element_a", "Current active power (element a)"),
    ("instantaneous_active_power_element_b", "Current active power (element b)"),
    ("read_element_a", "Current read on element A"),
    ("read_element_b", "Current read on element B"),
    ("read", "Current read - will read all available for meter type"),
    ("backlight", "Backlight setting"),
    ("load_switch", "Load switch setting"),
    ("prepay_enabled", "Is prepay mode enabled?"),
    (
        "daylight_savings_correction_enabled",
        "Is daylight savings correction enabled?",
    ),
    (
        "prepay_no_debt_recovery_when_emergency_credit_enabled",
        "Is no debt recovery in ecredit mode enabled?",
    ),
    (
        "prepay_no_standing_charge_when_power_fail_enabled",
        "Is no standing charge when power fail enabled?",
    ),
    ("prepay_balance", "Current prepay balance (if in prepay mode)"),
    (
        "prepay_transaction_count",
        "Count of prepay transactions (0 indexed so is num tx - 1)",
    ),
    ("three_phase_serial", "Three phase meter serial"),
    (
        "three_phase_instantaneous_voltage",
        "Current three phase voltage (if three phase meter)",
    ),
    ("three_phase_read", "Three phase reading"),
    ("three_phase_hardware_configuration", "Three phase hardware configuration"),
    ("tariffs_active_read", "Current tariff settings"),
    ("tariffs_future_read", "Future tariff settings"),
    (
        "tariffs_time_switches_element_a_or_single_read",
        "Time switches for element A",
    ),
    ("tariffs_time_switches_element_b_read", "Time switches for element B"),
]

"""
    This is a CLI wrapper around the mediator client v2.
"""


class EMOPCLI_V2(EmliteMediatorClientV2):
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

            if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_ACCESS_TOKEN:
                raise Exception(
                    "SUPABASE_URL, SUPABASE_ANON_KEY and/or SUPABASE_ACCESS_TOKEN not set"
                )

            self.supabase = supa_client(
                str(SUPABASE_URL), str(SUPABASE_ANON_KEY), str(SUPABASE_ACCESS_TOKEN)
            )

            mediator_address = "0.0.0.0:50051"
            is_single_meter_app = False

            if serial is not None:
                result = (
                    self.supabase.table("meter_registry")
                    .select("id,esco,single_meter_app")
                    .eq("serial", serial)
                    .execute()
                )
                if len(as_list(result)) == 0:
                    err_msg = f"meter {serial} not found"
                    console.print(err_msg)
                    raise Exception(err_msg)

                meter = as_first_item(result)
                meter_id = meter["id"]
                esco_id = meter["esco"]
                is_single_meter_app = meter["single_meter_app"]

                esco_code = None
                if esco_id is not None:
                    result = (
                        self.supabase.schema("flows")
                        .table("escos")
                        .select("code")
                        .eq("id", esco_id)
                        .execute()
                    )
                    esco_code = as_first_item(result)["code"]

                containers = get_instance(
                    is_single_meter_app=is_single_meter_app,
                    esco=esco_code,
                    serial=serial,
                    region=FLY_REGION,
                    env=cast(str | None, ENV),
                )
                mediator_address = containers.mediator_address(meter_id, serial)
                if not mediator_address:
                    raise Exception("unable to get mediator address")

                # Show latest clock drift
                res = (
                    self.supabase.table("meter_shadows")
                    .select("clock_time_diff_seconds,clock_time_diff_synced_at")
                    .eq("id", meter_id)
                    .execute()
                )
                if as_list(res):
                    drift_raw = as_first_item(res).get("clock_time_diff_seconds")
                    drift = f"{drift_raw}" if drift_raw is not None else "unknown"

                    last_read_raw = as_first_item(res).get("clock_time_diff_synced_at")

                    last_read = f"{last_read_raw}" if last_read_raw is not None else "unknown"

                    if last_read_raw:
                        try:
                            dt = datetime.datetime.fromisoformat(
                                last_read_raw.replace("Z", "+00:00")
                            )
                            last_read = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        except Exception as e:
                            logging.warning(
                                f"Failed to parse capture timestamp '{last_read_raw}': {e}"
                            )

                    console.print(
                        f"Latest Clock Drift: {drift} seconds | Captured At: {last_read}",
                        style="cyan",
                        highlight=False,
                    )

            # Initialize V2 client (without meter_id, but with resolved address)
            super().__init__(
                mediator_address=mediator_address,
                use_cert_auth=is_single_meter_app,
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
    #   Supabase / Info Commands
    # =================================

    def serial_to_name(self) -> None:
        # Kept local as it's a pure registry lookup, or could use GetInfo?
        # Leaving as strict Supabase lookup for valid registry check
        serial = self.serial
        if not serial:
             raise ValueError("Serial required for serial_to_name")

        if not self.supabase:
             raise Exception("Supabase client not initialized")

        result = (
            self.supabase.table("meter_registry")
            .select("name")
            .eq("serial", serial)
            .execute()
        )
        if len(as_list(result)) == 0:
            msg = f"meter {serial} not found"
            console.print(msg)
            raise Exception(msg)

        print(as_first_item(result)["name"])

    def info(self) -> None:
        """Call the new InfoService GetInfo via the V2 client."""
        if not self.serial:
            raise ValueError("Serial required for info command")

        # Use the V2 client method method inherited from EmliteMediatorClientV2
        # which calls the gRPC service
        info_json = self.get_info(self.serial)
        # Parse it just to pretty print it
        try:
             data = json.loads(info_json)
             print(json.dumps(data, indent=2))
        except:
             print(info_json)


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


def valid_event_log_idx(idx: str | None) -> int:
    if idx is None:
        raise argparse.ArgumentTypeError("event log idx cannot be None")

    try:
        idx_int = int(idx)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid log_idx {idx}. Should be an int between 0-9."
        )

    if idx_int < 0 or idx_int > 9:
        raise argparse.ArgumentTypeError(
            f"Invalid log_idx {idx}. Must be in range 0-9."
        )

    return idx_int


def valid_decimal(rate: str | None) -> Decimal:
    if rate is None:
        raise argparse.ArgumentTypeError("rate cannot be None")
    try:
        return Decimal(rate)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Should be a floating point number."
        )


def valid_rate(rate: str | None) -> Decimal:
    rate_decimal: Decimal = valid_decimal(rate)

    if rate_decimal > 1.0:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Can't be greater than 1 GBP."
        )

    exponent_int: int = rate_decimal.as_tuple().exponent  # type: ignore[assignment]
    decimal_places = abs(exponent_int)
    if decimal_places > 5:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Emlite meters can only store up to 5 decimal places."
        )

    return rate_decimal


def valid_switch(bool_str: str) -> bool:
    bool_str_lc = bool_str.lower()
    if bool_str_lc == "on":
        return True
    elif bool_str_lc == "off":
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid flag string '{bool_str}'. Should be 'on' or 'off'."
        )


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
        return EmopMessage.BacklightSettingType.no_button_prepay_mode
    elif setting == "no_button_credit_mode":
        return EmopMessage.BacklightSettingType.no_button_credit_mode
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid or unsupported load switch setting string '{setting}'. See choices with -h."
        )


def add_arg_serial(parser: argparse.ArgumentParser) -> None:
    """Adds optional positional argument serial"""
    parser.add_argument("serial", help="meter serial", nargs="?")


def args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

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

    subparsers.add_parser("version", help="Show version")

    subparsers.add_parser("env_show", help="Show current environment context")
    subparsers.add_parser(
        "env_set",
        help="Set CLI environment context [points ~/.simt/emlite.env at ~/.simt/emlite.<env>.env]",
    ).add_argument("env")

    # New command for getting all meters
    subparsers.add_parser("get_meters", help="Get list of meters (via InfoService)")


    # ===========    Simple Reads (no args)    ==========

    for cmd_tuple in SIMPLE_READ_COMMANDS:
        cmd_parser = subparsers.add_parser(cmd_tuple[0], help=cmd_tuple[1])
        add_arg_serial(cmd_parser)

    # ===========    Event logs     ==========

    event_log_parser = subparsers.add_parser(
        "event_log",
        help="Read a block of 10 events from the event log at a given index",
    )
    event_log_parser.add_argument(
        "log_idx",
        type=valid_event_log_idx,
        help="value 0-9 where 0 returns the latest 10 log entries; 9 the oldest 10 entries",
    )
    add_arg_serial(event_log_parser)

    # ===========    Profile logs (half hourly reads)    ==========

    profile_log_commands = [
        "profile_log_1",
        "profile_log_2",
    ]
    for cmd_str in profile_log_commands:
        profile_parser = subparsers.add_parser(
            cmd_str,
            description=f"""Fetch half hourly data for a given date time.

Example usage:

  emop -s EML1411222333 {cmd_str} --timestamp 2024-08-21T14:00
""",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_arg_serial(profile_parser)
        profile_parser.add_argument(
            "--timestamp",
            help="Timestamp in iso8601 format (eg. 2024-08-21 or 2024-08-21T14:00) of time to read profile logs for.",
            required=True,
            type=valid_iso_datetime,
        )

    # ===========    Three phase intervals (half hourly intervals)    ==========

    three_phase_intervals_parser = subparsers.add_parser(
        "three_phase_intervals",
        description="""Fetch three phase intervals for given time range.

Example usage:

emop -s EML1411222333 three_phase_intervals --start-time "2025-02-20T00:00+00" --end-time "2025-02-21T00:00+00"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_arg_serial(three_phase_intervals_parser)
    three_phase_intervals_parser.add_argument(
        "--day",
        help="Date to pull intervals for.",
        required=False,
        type=valid_iso_datetime,
    )
    three_phase_intervals_parser.add_argument(
        "--start-time",
        help="Start date time for intervals range.",
        required=False,
        type=valid_iso_datetime,
    )
    three_phase_intervals_parser.add_argument(
        "--end-time",
        help="End date time for intervals range.",
        required=False,
        type=valid_iso_datetime,
    )
    three_phase_intervals_parser.add_argument(
        "--csv",
        help="Path to CSV file to output intervals data",
        required=True,
        type=str,
    )
    three_phase_intervals_parser.add_argument(
        "--include_statuses",
        help="Include statuses in the CSV",
        required=False,
        action="store_true",
    )

    # ===========    generic obis read    ==========

    obis_read_parser = subparsers.add_parser(
        "obis_read", help="read a payload from an arbitrary obis / object id"
    )
    add_arg_serial(obis_read_parser)
    obis_read_parser.add_argument(
        "obis",
        help="obis / objectid to read",
    )

    # ===========    Writes    ==========

    clock_write_parser = subparsers.add_parser(
        "clock_time_write", help="Update clock time with current timestamp"
    )
    add_arg_serial(clock_write_parser)

    prepay_enabled_write_parser = subparsers.add_parser(
        "prepay_enabled_write", help="Set prepay mode flag"
    )
    add_arg_serial(prepay_enabled_write_parser)
    prepay_enabled_write_parser.add_argument(
        "enabled",
        type=valid_switch,
        help="set prepay flag (on=prepay mode, off=credit mode)",
    )

    prepay_send_token_parser = subparsers.add_parser(
        "prepay_send_token",
        help="Write a prepay token to the meter to topup the balance",
    )
    add_arg_serial(prepay_send_token_parser)
    prepay_send_token_parser.add_argument(
        "token", help="prepay token obtained from topupmeters.co.uk"
    )

    daylight_savings_correction_enabled_write_parser = subparsers.add_parser(
        "daylight_savings_correction_enabled_write",
        help="Set daylight_savings_correction flag",
    )
    add_arg_serial(daylight_savings_correction_enabled_write_parser)
    daylight_savings_correction_enabled_write_parser.add_argument(
        "enabled",
        type=valid_switch,
        help="set daylight_savings_correction flag (on, off)",
    )

    backlight_write_parser = subparsers.add_parser(
        "backlight_write",
        help="Write backlight setting to meter",
        description="""Supported settings:

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
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_arg_serial(backlight_write_parser)
    backlight_write_parser.add_argument(
        "setting",
        help="new backlight setting",
        type=valid_backlight_setting,
    )

    load_switch_write_parser = subparsers.add_parser(
        "load_switch_write",
        help="Write load_switch setting to meter",
        description="""Supported settings:
    normal_button_always
    no_button_prepay_mode
    no_button_credit_mode
    never_button_required

Example usage:

emop -s EML1411222333 load_switch_write never_button_required
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_arg_serial(load_switch_write_parser)
    load_switch_write_parser.add_argument(
        "setting",
        help="new load_switch setting",
        type=valid_load_switch_setting,
    )

    obis_write_parser = subparsers.add_parser(
        "obis_write", help="Write a payload to an arbitrary obis / object id"
    )
    add_arg_serial(obis_write_parser)
    obis_write_parser.add_argument(
        "obis",
        help="obis / objectid to read",
    )
    obis_write_parser.add_argument(
        "payload_hex",
        help="payload to write to obis (hex string)",
    )

    # ===========      Tariff Writes    ==========

    tariff_write_parser = subparsers.add_parser(
        "tariffs_future_write",
        help="Write future tariffs to meter",
        description="""Write future dated tariffs and emergency credit properties into the meter.

Example usage:

emop -s EML1411222333 tariffs_future_write \
        --from-ts "2024-08-21T06:54:00+00" \
        --unit-rate "0.23812" \
        --standing-charge "0.6975" \
        --ecredit-availability "10.0" \
        --debt-recovery-rate "0.25" \
        --emergency-credit "15.00"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_arg_serial(tariff_write_parser)
    tariff_write_parser.add_argument(
        "--from-ts",
        help="Date and time in iso8601 format of when the date tariff will apply from. NOTE: this is a clock time meaning in summer the BST time should be used here. If however a meter was configured with the daylight savings flag UNCHECKED then it should be UTC.",
        required=True,
        type=valid_iso_datetime,
    )
    tariff_write_parser.add_argument(
        "--unit-rate",
        help="Tariff unit rate (eg. '0.25' is 25 pence)",
        required=True,
        type=valid_rate,
    )
    tariff_write_parser.add_argument(
        "--standing-charge",
        help="Tariff standing charge (eg. '0.695' is 69.5 pence)",
        required=True,
        type=valid_rate,
    )
    tariff_write_parser.add_argument(
        # "--ec",
        "--emergency-credit",
        help="Emergency credit level (eg. '15.00' is 15 GBP)",
        required=False,
        default=Decimal("15.00"),
        type=valid_decimal,
    )
    tariff_write_parser.add_argument(
        # "--ea",
        "--ecredit-availability",
        help="Emergency credit availability level. EC button can be pressed when balance goes under this. (eg. '10.00' is 10 GBP)",
        required=False,
        default=Decimal("10.00"),
        type=valid_decimal,
    )
    tariff_write_parser.add_argument(
        # "-drr",
        "--debt-recovery-rate",
        help="Daily rate of debt recovery (eg. '0.3' is 30 pence)",
        required=False,
        default=Decimal("0.30"),
        type=valid_decimal,
    )

    # ===========    Info lookups    ==========

    info_parser = subparsers.add_parser(
        "info", help="metadata and shadows data for a meter"
    )
    add_arg_serial(info_parser)

    # serial_to_name command (retained)
    serial_to_name_parser = subparsers.add_parser(
         "serial_to_name", help="lookup meter name from serial"
    )
    add_arg_serial(serial_to_name_parser)

    return parser


def run_command(serial: str | None, command: str, kwargs: Dict[str, Any]) -> None:
    log_level = kwargs.pop("log_level", None)

    verbose = kwargs.pop("verbose", False)
    if verbose is True:
        log_level = logging.DEBUG

    try:
        with console.status(f"[bold green]Running {command}...", spinner="dots"):
            cli = EMOPCLI_V2(serial=serial, logging_level=log_level)
            method = getattr(cli, command)

            # INSPECT: Check if the method expects a 'serial' argument as the first parameter
            # EMOPCLI_V2 methods inherited from EmliteMediatorClientV2 mostly start with (self, serial, ...)
            # except those that don't need it.
            # Local methods like 'info' use 'self.serial' internally and don't take it as arg.
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            if params and params[0] == 'serial':
                if serial is None:
                     raise ValueError(f"Command '{command}' requires a serial number")
                result = method(serial, **kwargs)
            else:
                result = method(**kwargs)

        if result is not None:
            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, default=str))
            elif isinstance(result, (int, float, str, Decimal)):
                if command in [c[0] for c in SIMPLE_READ_COMMANDS]:
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


def main() -> None:
    # supress supabase py request logging and underlying noisy libs:
    suppress_noisy_loggers()

    parser = args_parser()

    # support autocompletion - see https://kislyuk.github.io/argcomplete
    argcomplete.autocomplete(parser)

    kwargs = vars(parser.parse_args())
    command = kwargs.pop("subparser")
    if command is None:
        parser.print_help()
        exit(-1)

    # CLI works on a given serial or list of serials.
    arg_s = kwargs.pop("s", None)
    arg_serial = kwargs.pop("serial", None)
    arg_serials = kwargs.pop("serials", None)
    arg_serials_file = kwargs.pop("serials_file", None)

    serial = arg_s or arg_serial
    try:
        # Commands that don't need a serial or can work without one
        if command in ["env_set", "env_show", "version", "get_meters"]:
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
