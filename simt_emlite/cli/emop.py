import argparse
import datetime
import importlib
import logging
import os
import subprocess
import sys
from decimal import Decimal

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config
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
    #   EMOP Commands Wrappers
    # =================================

    def tariffs_future_write_str_args(
        self, from_ts_iso_str: str, standing_charge_str: str, unit_rate_str: str
    ):
        self._check_amount_arg_is_string(standing_charge_str)
        self._check_amount_arg_is_string(unit_rate_str)
        self.tariffs_future_write(
            datetime.datetime.fromisoformat(from_ts_iso_str),
            standing_charge=Decimal(standing_charge_str),
            unit_rate=Decimal(unit_rate_str),
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

    def _check_amount_arg_is_string(self, arg_value):
        if isinstance(arg_value, str):
            return
        print(
            "\nERROR: amount argument passed as floating point number. pass "
            + "as string to avoid floating point rounding errors "
            + "[eg. \"'0.234'\" or '\"0.234\"']"
        )
        sys.exit(10)

    # =================================
    #   Utils
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

        config_path = os.path.join(os.path.expanduser("~"), ".simt")
        rt = subprocess.run(
            [
                "ln",
                "-s",
                "--force",
                os.path.join(config_path, f"emlite.{env}.env"),
                os.path.join(config_path, "emlite.env"),
            ],
            check=True,
            cwd=config_path,
        )

        if rt.returncode == 0:
            logging.info(f"env set to {env}")
        else:
            logging.info("failed to set env")

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


def main():
    logging.basicConfig(level=logging.INFO)
    # supress supabase py request logging:
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()
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

    simple_read_commands = [
        "csq",
        "hardware",
        "firmware_version",
        "serial",
        "clock_time",
        "instantaneous_voltage",
        "prepay_enabled",
        "prepay_balance",
        "prepay_transaction_count",
        "three_phase_instantaneous_voltage",
        "tariffs_active_read",
        "tariffs_future_read",
        "tariffs_time_switches_element_a_or_single_read",
        "tariffs_time_switches_element_b_read",
    ]
    for cmd in simple_read_commands:
        subparsers.add_parser(cmd).add_argument("serial", help="meter serial")

    profile_log_commands = [
        "profile_log_1",
        "profile_log_2",
    ]
    for cmd in profile_log_commands:
        profile_parser = subparsers.add_parser(
            cmd, help="Fetch half hourly date from a given date time."
        )
        profile_parser.add_argument("serial", help="meter serial")
        profile_parser.add_argument(
            "--timestamp",
            help="Date and time in iso8601 format of time to read profile logs from.",
            required=True,
            type=valid_iso_datetime,
        )

    kwargs = vars(parser.parse_args())

    command = kwargs.pop("subparser")
    if command is None:
        parser.print_help()
        exit(-1)

    logging.info(kwargs)

    serial = kwargs.pop("serial", None)
    cli = EMOPCLI(serial=serial)

    method = getattr(cli, command)
    method(**kwargs)


if __name__ == "__main__":
    main()
