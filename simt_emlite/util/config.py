import os
import sys

from dotenv import load_dotenv

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".simt")
EMOP_CONFIG_FILE = os.path.join(CONFIG_DIR, "emlite.env")


def load_config():
    if os.path.isfile(EMOP_CONFIG_FILE) is False:
        print(
            "ERROR: ~/.simt/emlite.env does not exist. See tool help for how to set this up."
        )
        sys.exit(5)

    load_dotenv(EMOP_CONFIG_FILE)

    return {
        "env": os.environ.get("ENV"),
        # supabase
        "supabase_url": os.environ.get("SUPABASE_URL"),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY"),
        "supabase_access_token": os.environ.get("SUPABASE_ACCESS_TOKEN"),
        # fly
        "fly_token": os.environ.get("FLY_API_TOKEN"),
        "fly_app": os.environ.get("FLY_APP"),
        # emnify gateway socks proxy
        "socks_host": os.environ.get("SOCKS_HOST"),
        "socks_port": os.environ.get("SOCKS_PORT"),
        "socks_username": os.environ.get("SOCKS_USERNAME"),
        "socks_password": os.environ.get("SOCKS_PASSWORD"),
        # mediator gateway
        "mediator_proxy_host": os.environ.get("MEDIATOR_PROXY_HOST"),
        # simt_emlite docker image
        "simt_emlite_image": os.environ.get("SIMT_EMLITE_IMAGE"),
        # site (optional)
        "site": os.environ.get("SITE"),
    }
