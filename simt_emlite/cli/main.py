import datetime
import sys
from decimal import Decimal

from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.util.supabase import supa_client
import fire

from simt_emlite.util.logging import get_logger
from dotenv import load_dotenv
import os

logger = get_logger(__name__, __file__)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".simt")
EMOP_CONFIG_FILE = os.path.join(CONFIG_DIR, "emop.env")

if os.path.isfile(EMOP_CONFIG_FILE) is False:
    print("ERROR: ~/.simt/emop.env does not exist. See tool help for how to set this up.")
    sys.exit(5)

load_dotenv(EMOP_CONFIG_FILE)
supabase_url = os.environ.get("SUPABASE_URL")
supabase_anon_key = os.environ.get("SUPABASE_KEY")
access_token = os.environ.get("JWT_ACCESS_TOKEN")


"""
    This is a CLI wrapper around the mediator client using Fire to generate the
    CLI interface from the client python interface.
"""


class EMOPCLI(EmliteMediatorClient):
    def __init__(self, serial=None, host=None, port=None):
        if (serial is not None):
            supabase = supa_client(supabase_url, supabase_anon_key, access_token) 
            result = (supabase.table('meter_registry')
                           .select('ip_address,id')
                           .eq('serial', serial)
                           .execute())
            
            if (len(result.data) == 0):
                logger.error("meter not found for given serial")
                sys.exit(10)

            # TODO: connection by serial will involve connecting to a proxy
            #       at a fixed remote address and port that will proxy to the
            #       appropriate mediator
            logger.error("connection remotely by serial not yet supported")
            sys.exit(10)

        if (port is not None):
            super().__init__(port=port)
    
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
        supabase = supa_client(supabase_url, supabase_anon_key, access_token) 
        result = (supabase.table('meter_registry')
                       .select('name')
                       .eq('serial', serial)
                       .execute())
        if (len(result.data) == 0):
            logger.info("meter not found for given serial")
            sys.exit()

        print(result.data[0]['name'])

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