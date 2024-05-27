import os
import sys

from dotenv import load_dotenv

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".simt")
EMOP_CONFIG_FILE = os.path.join(CONFIG_DIR, "emlite.env")

def load_config():
    if os.path.isfile(EMOP_CONFIG_FILE) is False:
        print("ERROR: ~/.simt/emlite.env does not exist. See tool help for how to set this up.")
        sys.exit(5)

    load_dotenv(EMOP_CONFIG_FILE)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_anon_key = os.environ.get("SUPABASE_KEY")
    access_token = os.environ.get("JWT_ACCESS_TOKEN")
    fly_app = os.environ.get("FLY_APP")

    return {
        "supabase_url": supabase_url,
        "supabase_anon_key": supabase_anon_key,
        "access_token": access_token,
        "fly_app": fly_app
    } 