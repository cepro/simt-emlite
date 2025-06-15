import os
import sys
import traceback

from dotenv import load_dotenv

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".simt")
EMOP_CONFIG_FILE = os.path.join(CONFIG_DIR, "emlite.env")


def load_config():
    if os.path.isfile(EMOP_CONFIG_FILE) is False:
        stack_trace = traceback.format_stack()
        print(
            "ERROR: ~/.simt/emlite.env does not exist. See tool help for how to set this up."
        )
        print(f"STACK: [{stack_trace}]")
        sys.exit(5)

    load_dotenv(EMOP_CONFIG_FILE)

    return {
        "env": os.environ.get("ENV"),
        # supabase
        "supabase_url": os.environ.get("SUPABASE_URL"),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY"),
        "supabase_access_token": os.environ.get("SUPABASE_ACCESS_TOKEN"),
        # fly
        "fly_api_token": os.environ.get("FLY_API_TOKEN"),
        "fly_dns_server": os.environ.get("FLY_DNS_SERVER"),
        # emnify gateway socks proxy
        "socks_host": os.environ.get("SOCKS_HOST"),
        "socks_port": os.environ.get("SOCKS_PORT"),
        "socks_username": os.environ.get("SOCKS_USERNAME"),
        "socks_password": os.environ.get("SOCKS_PASSWORD"),
        # simt_emlite docker image
        "simt_emlite_image": os.environ.get("SIMT_EMLITE_IMAGE"),
        # mediator
        "mediator_inactivity_seconds": os.environ.get("MEDIATOR_INACTIVITY_SECONDS"),
    }


def set_config(env: str):
    config_path = os.path.join(os.path.expanduser("~"), ".simt")
    target_path = os.path.join(config_path, "emlite.env")
    source_path = os.path.join(config_path, f"emlite.{env}.env")

    if os.path.exists(target_path):
        os.unlink(target_path)

    os.symlink(source_path, target_path)
