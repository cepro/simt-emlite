import json
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
        self.machines = API(FLY_API_TOKEN)

    def list(self, metadata_filter: tuple[str, str] = None):
        return self.machines.list(FLY_APP, metadata_filter=metadata_filter)

    def create(self, serial: str):
        meter = self._meter_by_serial(serial)
        result = self.machines.create(
            FLY_APP,
            SIMT_EMLITE_IMAGE,
            ["simt_emlite.mediator.grpc.server"],
            name=f"mediator-{serial}",
            env_vars={
                "EMLITE_HOST": meter["ip_address"],
                "SOCKS_HOST": SOCKS_HOST,
                "SOCKS_PORT": SOCKS_PORT,
                "SOCKS_USERNAME": SOCKS_USERNAME,
                "SOCKS_PASSWORD": SOCKS_PASSWORD,
            },
            metadata={"meter_id": meter["id"]},
        )
        logger.info(json.dumps(result, indent=2, sort_keys=True))
        return result

    def start_one(self, serial: str):
        machine_id = self._machine_id_by_serial(serial)
        self.machines.start(FLY_APP, machine_id)
        return machine_id

    def start_many(self, meter_ids: List[str]) -> Dict[str, int]:
        pass

    def start_all(self) -> Dict[str, int]:
        pass

    def stop_all(self):
        pass

    def destroy_all(self):
        pass

    def wait_one(self, machine_id: str):
        self.machines.wait(FLY_APP, machine_id, "started")

    def destroy_one(self, serial: str):
        machine_id, instance_id = self.stop_one(serial)
        self.machines.wait(FLY_APP, machine_id, instance_id, "stopped")
        self.machines.destroy(FLY_APP, machine_id)

    def stop_one(self, serial: str) -> str:
        machine = self._machine_by_serial(serial)
        self.machines.stop(FLY_APP, machine["id"])
        return machine["id"], machine["instance_id"]

    def _machine_by_serial(self, serial):
        meter = self._meter_by_serial(serial)
        machines = self.list(("meter_id", meter["id"]))
        if len(machines) == 0:
            raise Exception(f"machine for meter {serial} not found")
        return machines[0]

    def _machine_id_by_serial(self, serial):
        machine = self._machine_by_serial(serial)
        return machine["id"]

    def _meter_by_serial(self, serial) -> str:
        result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address")
            .eq("serial", serial)
            .execute()
        )
        if len(result.data) == 0:
            logger.error(f"meter {serial} not found")
            sys.exit(10)

        return result.data[0]


def main():
    fire.Fire(MediatorsCLI)


if __name__ == "__main__":
    main()
