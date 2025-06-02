import argparse
import datetime
import importlib
import json
import logging
import os
import sys
from decimal import Decimal
from typing import Any, Dict, List

import argcomplete
from emop_frame_protocol.emop_message import EmopMessage

from simt_emlite.mediator.client import EmliteMediatorClient, MediatorClientException
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config, set_config
from simt_emlite.util.supabase import supa_client

config = load_config()

SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
SUPABASE_ANON_KEY = config["supabase_anon_key"]
SUPABASE_URL = config["supabase_url"]

# Not using proxy currently:

# PROXY_HOST = config["mediator_proxy_host"]
# PROXY_CERT = get_cert()

FLY_API_TOKEN = config["fly_api_token"]


"""
    This is a CLI wrapper around the mediator client.
"""


class EMOPCLI(EmliteMediatorClient):
    def __init__(self, serial=None, emnify_id=None):
        self.serial = serial

        # TODO: necessary for meters that have not yet had a serial read
        #       they will be in the registry but with a NULL serial
        if emnify_id is not None:
            err_msg = "emnify_id lookup is not yet supported."
            print(err_msg)
            raise Exception(err_msg)

        self.supabase = supa_client(
            SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_ACCESS_TOKEN
        )

        if serial is not None:
            result = (
                self.supabase.table("meter_registry")
                .select("id,esco")
                .eq("serial", serial)
                .execute()
            )
            if len(result.data) == 0:
                err_msg = f"meter {serial} not found"
                print(err_msg)
                raise Exception(err_msg)

            meter_id = result.data[0]["id"]
            esco_id = result.data[0]["esco"]

            esco_code = None
            if esco_id is not None:
                result = (
                    self.supabase.schema("flows")
                    .table("escos")
                    .select("code")
                    .eq("id", esco_id)
                    .execute()
                )
                esco_code = result.data[0]["code"]

            containers = get_instance(esco=esco_code, serial=serial)
            mediator_address = containers.mediator_address(meter_id, serial)
            print(f"mediator_address {mediator_address}")

            super().__init__(
                mediator_address=mediator_address,
                meter_id=meter_id,
                # access_token=SUPABASE_ACCESS_TOKEN,
                # proxy_host_override=PROXY_HOST,
                # proxy_cert_override=PROXY_CERT,
            )

    # =================================
    #   Supabase Commands
    # =================================

    def serial_to_name(self, serial: str):
        result = (
            self.supabase.table("meter_registry")
            .select("name")
            .eq("serial", serial)
            .execute()
        )
        if len(result.data) == 0:
            msg = f"meter {serial} not found"
            print(msg)
            raise Exception(msg)

        print(result.data[0]["name"])

    def info(self):
        result = (
            self.supabase.table("meter_registry")
            .select("*")
            .eq("serial", self.serial)
            .execute()
        )
        if len(result.data) == 0:
            msg = f"meter {self.serial} not found"
            print(msg)
            raise Exception(msg)
        registry_rec = result.data[0]

        result = (
            self.supabase.table("meter_shadows")
            .select("*")
            .eq("id", registry_rec["id"])
            .execute()
        )
        shadow_rec = result.data[0]

        print(json.dumps({"registry": registry_rec, "shadow": shadow_rec}, indent=2))

    # =================================
    #   Tool related
    # =================================

    def version(self):
        version = importlib.metadata.version("simt-emlite")
        logging.info(version)

    def env_show(self):
        logging.info(config["env"])

    def env_set(self, env: str):
        allowed_env = ["prod", "qa", "local"]
        if env not in allowed_env:
            logging.info(f"ERROR: env must be one of {allowed_env}")
            sys.exit(1)
        set_config(env)
        logging.info(f"env set to {env}")

    # =================================
    #   Shelved for now
    # =================================

    # NOTE: initially implemented the below to support login by user/password
    #  with Supabase. However this mechanism requires auth.users user and RLS
    #  based authorization. As we want to access flows tables which are FDWs
    #  this doesn't work.  So for now at least we generate a postgres role and
    #  a JWT for it and set up the auth rules using postgres roles and grants.
    #  JWT is checked by supabase (postgrest) but does not use auth.users
    #  or the authenticated role.

    # def login(self, email: str, password: str):
    #     supabase = supa_client(supabase_url, supabase_anon_key)
    #     result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    #     self._save_tokens(result.session.access_token, result.session.refresh_token)

    # def logout(self, email: str, password: str):
    #     supabase = supa_client(supabase_url, supabase_anon_key)
    #     result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    #     print(result)

    # def _save_tokens(self, access_token: str, refresh_token: str):
    #     with open(SUPABASE_TOKEN_FILE, "w") as env_file:
    #         env_file.write(f"# Supabase logged in user JWT tokens\n")
    #         env_file.write(f"access_token={access_token}\n")
    #         env_file.write(f"refresh_token={refresh_token}\n")

    # def _read_tokens(self):
    #     return dotenv_values(SUPABASE_TOKEN_FILE)


def valid_iso_datetime(timestamp: str):
    try:
        return datetime.datetime.fromisoformat(timestamp)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid ISO datetime format: {timestamp}")


def valid_event_log_idx(idx: str):
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


def valid_decimal(rate: str):
    try:
        return Decimal(rate)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Should be a floating point number."
        )


def valid_rate(rate: str):
    rate_decimal = valid_decimal(rate)

    if rate_decimal > 1.0:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Can't be greater than 1 GBP."
        )

    decimal_places = abs(rate_decimal.as_tuple().exponent)
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


def add_arg_serial(parser):
    """Adds optional positional argument serial"""
    parser.add_argument("serial", help="meter serial", nargs="?")


def args_parser():
    parser = argparse.ArgumentParser()
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
    ).add_argument(
        "env",
        choices=["prod", "qa", "local"],
    )

    # ===========    Simple Reads (no args)    ==========

    simple_read_commands = [
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
    for cmd in simple_read_commands:
        cmd_parser = subparsers.add_parser(cmd[0], help=cmd[1])
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
    for cmd in profile_log_commands:
        profile_parser = subparsers.add_parser(
            cmd,
            description=f"""Fetch half hourly data for a given date time.

Example usage:

  emop -s EML1411222333 {cmd} --timestamp 2024-08-21
""",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        add_arg_serial(profile_parser)
        profile_parser.add_argument(
            "--timestamp",
            help="Date in iso8601 format (eg. 2024-08-21) of date to read profile logs for.",
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
        "--start-time",
        help="Start date time for intervals range.",
        required=True,
        type=valid_iso_datetime,
    )
    three_phase_intervals_parser.add_argument(
        "--end-time",
        help="End date time for intervals range.",
        required=True,
        type=valid_iso_datetime,
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

    # ===========      Tariff Writes    ==========

    tariff_write_parser = subparsers.add_parser(
        "tariffs_future_write",
        help="Write future tariffs to meter",
        description="""Write future dated tariffs and emergency credit properties into the meter.

Example usage:

emop -s EML1411222333 tariffs_future_write \\
        --from-ts "2024-08-21T06:54:00+00" \\
        --unit-rate "0.23812" \\
        --standing-charge "0.6975" \\
        --ecredit-availability "10.0" \\
        --debt-recovery-rate "0.25" \\
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

    # ===========    Supabase lookups    ==========

    info_parser = subparsers.add_parser(
        "info", help="metadata and shadows data for a meter"
    )
    add_arg_serial(info_parser)

    return parser


def run_command(serial: str, command: str, kwargs: Dict[str, Any]):
    try:
        cli = EMOPCLI(serial=serial)
    except Exception:
        # just return - we assume the error was logged by the constructor
        return

    method = getattr(cli, command)
    try:
        method(**kwargs)
    except MediatorClientException as e:
        if e.code_str == "EMLITE_CONNECTION_FAILURE":
            logging.error("Failed to connect to meter")
        else:
            logging.error(f"Failure [{e}]")


def run_command_for_serials(
    serial_list: List[str], command: str, kwargs: Dict[str, Any]
):
    for serial in serial_list:
        logging.info(f"\nrunning '{command}' for meter {serial} ...\n")
        run_command(serial, command, kwargs)


def main():
    logging.basicConfig(level=logging.INFO)
    # supress supabase py request logging:
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = args_parser()

    # support autocompletion - see https://kislyuk.github.io/argcomplete
    argcomplete.autocomplete(parser)

    kwargs = vars(parser.parse_args())
    command = kwargs.pop("subparser")
    if command is None:
        parser.print_help()
        exit(-1)

    # logging.info(kwargs)

    # cli works on a given serial or list of serials.
    #
    # there are 4 ways to specify serials:
    #  * emop -s <serial> csq
    #  * emop csq <serial>
    #  * emop --serials <serial1,serial2,...> csq
    #  * emop --serials-file serials.txt csq
    #
    # pop off all serial argument possibilities so they are removed from
    # kwargs. then use first seen in the order documented above.
    arg_s = kwargs.pop("s", None)
    arg_serial = kwargs.pop("serial", None)
    arg_serials = kwargs.pop("serials", None)
    arg_serials_file = kwargs.pop("serials_file", None)

    serial = arg_s or arg_serial
    if serial or command in ["env_set", "env_show", "version", "info"]:
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
        parser.print_help()
        exit(-1)


if __name__ == "__main__":
    main()
