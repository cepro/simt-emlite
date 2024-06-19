import sys
from typing import Dict, List

import fire
from simt_fly_machines.api import API

from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

config = load_config()

SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
SUPABASE_ANON_KEY = config["supabase_anon_key"]
SUPABASE_URL = config["supabase_url"]

FLY_API_TOKEN = config["fly_token"]
FLY_APP = config["fly_app"]

SOCKS_HOST = config["socks_host"]
SOCKS_PORT = config["socks_port"]
SOCKS_USERNAME = config["socks_username"]
SOCKS_PASSWORD = config["socks_password"]

SIMT_EMLITE_IMAGE = config["simt_emlite_image"]

"""
    This is a CLI for managing Emlite mediator processes.
"""


class MediatorsCLI:
    def __init__(self):
        self.supabase = supa_client(
            SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_ACCESS_TOKEN
        )
        logger.info(config)

        self.machines = API(FLY_API_TOKEN)

    def list(self):
        self.machines.list(FLY_APP)

    def start_one(self, serial: str):
        meter = self._meter_by_serial(serial)
        self.machines.create(
            FLY_APP,
            SIMT_EMLITE_IMAGE,
            ["simt_emlite.mediator.grpc.server"],
            name=f"mediator-{serial}",
            env_vars={"EMLITE_HOST": meter["ip_address"]},
            metadata={"meter_id": meter["id"]},
        )

    def start_many(self, meter_ids: List[str]) -> Dict[str, int]:
        pass

    def start_all(self) -> Dict[str, int]:
        pass

    def stop_all(self):
        pass

    def remove_all(self):
        pass

    def stop_one(self, meter_id: str):
        pass

    def _meter_by_serial(self, serial):
        result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address")
            .eq("serial", serial)
            .execute()
        )
        if len(result.data) == 0:
            logger.error("meter not found for given serial")
            sys.exit(10)

        return result.data


def main():
    fire.Fire(MediatorsCLI)


if __name__ == "__main__":
    main()
