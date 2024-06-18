import datetime
import sys
from decimal import Decimal

import fire

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)


config = load_config()

ACCESS_TOKEN = config["ACCESS_TOKEN"]
SUPABASE_ANON_KEY = config["SUPABASE_ANON_KEY"]
SUPABASE_URL = config["SUPABASE_URL"]

PROXY_HOST = config["MEDIATOR_PROXY_HOST"]
with open(config["PROXY_CERT_PATH"], "rb") as cert_file:
    PROXY_CERT = cert_file.read()


"""
    This is a CLI wrapper around the mediator client using Fire to generate the
    CLI interface from the client python interface.
"""


class EMOPCLI(EmliteMediatorClient):
    def __init__(self, serial, emnify_id=None):
        # TODO: necessary for meters that have not yet had a serial read
        #       they will be in the registry but with a NULL serial
        if emnify_id is not None:
            err_msg = "emnify_id lookup is not yet supported."
            logger.warn(err_msg)
            raise Exception(err_msg)

        # serial mandatory until emnify_id supported above
        if serial is None:
            err_msg = "serial property required at this stage"
            logger.warn(err_msg)
            raise Exception(err_msg)

        self.supabase = supa_client(SUPABASE_URL, SUPABASE_ANON_KEY, ACCESS_TOKEN)

        result = (
            self.supabase.table("meter_registry")
            .select("id")
            .eq("serial", serial)
            .execute()
        )

        if len(result.data) == 0:
            logger.error("meter not found for given serial")
            sys.exit(10)

        meter_id = result.data["id"]
        mediator_host = f"mediator-{serial}"

        super().__init__(
            mediator_host=mediator_host,
            access_token=ACCESS_TOKEN,
            meter_id=meter_id,
            proxy_host_override=PROXY_HOST,
            proxy_cert_override=PROXY_CERT,
        )

    # =================================
    #   EMOP Commands Wrappers
    # =================================

    def profile_log_1_str_args(self, ts_iso_str: str):
        return self.profile_log_1(
            datetime.datetime.fromisoformat(ts_iso_str),
        )

    def profile_log_2_str_args(self, ts_iso_str: str):
        return self.profile_log_2(
            datetime.datetime.fromisoformat(ts_iso_str),
        )

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
            logger.info("meter not found for given serial")
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


def main():
    fire.Fire(EMOPCLI)


if __name__ == "__main__":
    main()
