import argparse
import datetime
import importlib
import logging
import sys
from decimal import Decimal

import argcomplete

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
                print(f"meter {serial} not found")
                sys.exit(10)

            meter_id = result.data[0]["id"]
            esco_id = result.data[0]["esco"]

            result = (
                self.supabase.schema("flows")
                .table("escos")
                .select("code")
                .eq("id", esco_id)
                .execute()
            )
            esco_code = result.data[0]["code"]

            containers = get_instance(esco_code)
            mediator_address = containers.mediator_address(meter_id, serial)

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
            print(f"meter {serial} not found")
            sys.exit()

        print(result.data[0]["name"])

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


def valid_decimal(rate: str):
    try:
        return Decimal(rate)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Should be a floating point number."
        )


def valid_rate(rate: str):
    rate_dec = valid_decimal(rate)
    if rate_dec > 1.0:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Can't be greater than 1 GBP."
        )
    return rate_dec


def valid_switch(bool_str: str):
    bool_str_lc = bool_str.lower()
    if bool_str_lc == "on":
        return True
    elif bool_str_lc == "off":
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid flag string '{bool_str}'. Should be 'on' or 'off'."
        )


def add_arg_serial(parser):
    """Adds optional positional argument serial"""
    parser.add_argument("serial", help="meter serial", nargs="?")


def args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", help="Serial", required=False)

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
        ("serial", "Meter serial"),
        ("clock_time_read", "Current clock time on the meter"),
        ("instantaneous_voltage", "Current voltage"),
        ("read_element_a", "Current read on element A"),
        ("read_element_b", "Current read on element B"),
        ("prepay_enabled", "Is prepay mode enabled?"),
        ("prepay_balance", "Current prepay balance (if in prepay mode)"),
        ("prepay_transaction_count", "Count of prepay transactions"),
        ("three_phase_serial", "Three phase meter serial"),
        (
            "three_phase_instantaneous_voltage",
            "Current three phase voltage (if three phase meter)",
        ),
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

    # ===========    Profile logs (half hourly reads)    ==========

    profile_log_commands = [
        "profile_log_1",
        "profile_log_2",
    ]
    for cmd in profile_log_commands:
        profile_parser = subparsers.add_parser(
            cmd, help="Fetch half hourly date from a given date time."
        )
        add_arg_serial(profile_parser)
        profile_parser.add_argument(
            "--timestamp",
            help="Date and time in iso8601 format of time to read profile logs from.",
            required=True,
            type=valid_iso_datetime,
        )

    # ===========    Clock write    ==========

    clock_write_parser = subparsers.add_parser(
        "clock_time_write", help="Update clock time with current timestamp"
    )
    add_arg_serial(clock_write_parser)

    # ===========      Tariff Writes    ==========

    tariff_write_parser = subparsers.add_parser(
        "tariffs_future_write",
        description="""Write future dated tariffs and emergency credit properties into the meter.

Example usage:

emop -s EML1411222333 tariffs_future_write \\
        --from-ts "2024-08-21T06:54:00" \\
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
        help="Date and time in iso8601 format of when the date tariff will apply from.",
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

    # ===========      Prepay Writes    ==========

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

    return parser


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

    # supporting either -s <serial> or positional argument <serial> after commands
    # pop both off so they are removed from kwargs.
    # use -s if it's there otherwise the positional.
    arg_s = kwargs.pop("s", None)
    arg_serial = kwargs.pop("serial", None)
    serial = arg_s or arg_serial

    cli = EMOPCLI(serial=serial)

    method = getattr(cli, command)
    try:
        method(**kwargs)
    except MediatorClientException as e:
        if e.code_str == "EMLITE_CONNECTION_FAILURE":
            logging.error("Failed to connect to meter")
        else:
            logging.error(f"Failure [{e}]")


if __name__ == "__main__":
    main()
