import json
import sys
from datetime import datetime
from typing import Dict, List, Literal, Union

import fire
from simt_fly_machines.api import API

from simt_emlite.util.config import load_config
from simt_emlite.util.supabase import Client, supa_client

# merge this with ContainerState when merging with orchestrate.mediators module
MACHINE_STATE_TYPE = Union[
    Literal["started"], Literal["stopped"], Literal["suspended"], Literal["destroyed"]
]

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

LOG_TIMES = False


def log(msg):
    if LOG_TIMES:
        print(f"{datetime.now().strftime('%S.%f')} {msg}")


class MediatorsCLI:
    def __init__(self):
        log("top __init__")
        self.supabase: Client = supa_client(
            SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_ACCESS_TOKEN
        )
        self.machines = API(FLY_API_TOKEN)
        log("bottom __init__")

    def list(
        self,
        site: str = None,
        machine_state: Union[MACHINE_STATE_TYPE] = None,
        show_all=False,
    ) -> List:
        """
        List meters and corresponding machines

        Args:
            site: site code [eg. 'hmce' for Hazelmead]
            machine_state: one of [started, stopped, suspended, destroyed]
            show_all: show all meters [True | False]
        """
        log("top list - get sites:")
        sites_result = self.supabase.table("sites").select("id,code").execute()
        log("got sites - get meters")
        site_id_to_code = {s["id"]: s["code"] for s in sites_result.data}
        site_code_to_id = {s["code"]: s["id"] for s in sites_result.data}

        meters_query = self.supabase.table("meter_registry").select(
            "id,ip_address,serial,site"
        )
        if site is not None:
            site_lc = site.lower()
            if site_lc not in site_code_to_id:
                print(f"unknown site [{site_lc}]")
                sys.exit(1)
            meters_query.eq("site", site_code_to_id[site_lc])

        meters_result = meters_query.execute()
        log("got meters")

        # meter result with site id replaced with site code
        meters = [{**m, "site": site_id_to_code[m["site"]]} for m in meters_result.data]

        log("before get machines")

        # add machine data
        machines = self.machines.list(
            FLY_APP,
            #  metadata_filter=metadata_filter
        )

        for meter in meters:
            machine_matches = list(
                filter(
                    lambda m: m["config"]["metadata"]["meter_id"] == meter["id"],
                    machines,
                )
            )
            machine = machine_matches[0] if len(machine_matches) != 0 else None

            machine_dict = None
            if machine is not None:
                machine_dict = {}
                machine_dict["id"] = machine["id"]
                machine_dict["name"] = machine["name"]
                machine_dict["state"] = machine["state"]
                machine_dict["image"] = machine["config"]["image"]
            meter["machine"] = machine_dict

        if machine_state is not None:
            meters = list(
                filter(
                    lambda m: m["machine"] is not None
                    and m["machine"]["state"] == machine_state,
                    meters,
                )
            )

        log("bottom list")
        return json.dumps(meters, indent=2, sort_keys=True)

    def create(self, serial: str):
        meter = self._meter_by_serial(serial)

        machine_name = f"mediator-{serial}"
        machine_metadata = {"meter_id": meter["id"]}

        answer = input(f"""
Fly App:    {FLY_APP}
Image:      {SIMT_EMLITE_IMAGE}
Name:       {machine_name}
Metadata:   {machine_metadata}

Create machine with these details (Y/n): """)
        if answer != "Y":
            sys.exit(1)

        result = self.machines.create(
            FLY_APP,
            SIMT_EMLITE_IMAGE,
            ["simt_emlite.mediator.grpc.server"],
            name=machine_name,
            env_vars={
                "EMLITE_HOST": meter["ip_address"],
                "SOCKS_HOST": SOCKS_HOST,
                "SOCKS_PORT": SOCKS_PORT,
                "SOCKS_USERNAME": SOCKS_USERNAME,
                "SOCKS_PASSWORD": SOCKS_PASSWORD,
            },
            metadata=machine_metadata,
        )
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
            print(f"meter {serial} not found")
            sys.exit(10)

        return result.data[0]


def main():
    fire.Fire(MediatorsCLI)


if __name__ == "__main__":
    main()
