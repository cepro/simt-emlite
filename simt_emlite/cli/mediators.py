import os
import subprocess
import sys
from datetime import datetime
from json import dumps
from typing import Dict, List, Literal, Union

import fire
from rich import box
from rich.console import Console
from rich.table import Table
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
        esco: str = None,
        machine_state: Union[MACHINE_STATE_TYPE] = None,
        machine: bool = None,
        no_machine: bool = None,
        json=False,
        show_all=False,
    ) -> List:
        """
        List meters and corresponding machines

        Args:
            esco: esco code [eg. 'hmce' for Hazelmead]
            machine_state: one of [started, stopped, suspended, destroyed]
            machine: show only with machines
            no_machine: show meters without machines
            show_all: show all meters [True | False]
        """
        meters = self._list(
            esco=esco,
            machine_state=machine_state,
            machine=machine,
            no_machine=no_machine,
            show_all=show_all,
        )

        if json is True:
            print(dumps(meters, indent=2))
            return

        table = Table(
            "esco", "serial", "machine state", "machine image", box=box.SQUARE
        )

        for meter in meters:
            row_values = [meter["esco"], meter["serial"]]
            if meter["machine"] is not None:
                row_values.append(meter["machine"]["state"])
                row_values.append(meter["machine"]["image"])
            table.add_row(*row_values)

        console = Console()
        console.print(table)

    def _list(
        self,
        esco: str = None,
        machine_state: Union[MACHINE_STATE_TYPE] = None,
        machine: bool = None,
        no_machine: bool = None,
        show_all=False,
    ) -> List:
        escos_result = self.supabase.table("escos").select("id,code").execute()

        esco_id_to_code = {e["id"]: e["code"] for e in escos_result.data}
        esco_code_to_id = {e["code"]: e["id"] for e in escos_result.data}

        meters_query = (
            self.supabase.table("meter_registry")
            .select("id,ip_address,serial,esco")
            .eq("mode", "active")
        )

        if esco is not None:
            esco_lc = esco.lower()
            if esco_lc not in esco_code_to_id:
                print(f"unknown esco [{esco_lc}]")
                sys.exit(1)
            meters_query.eq("esco", esco_code_to_id[esco_lc])

        meters_result = meters_query.execute()

        # meter result with esco id replaced with esco code
        meters = [{**m, "esco": esco_id_to_code[m["esco"]]} for m in meters_result.data]

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
            mach = machine_matches[0] if len(machine_matches) != 0 else None

            machine_dict = None
            if mach is not None:
                machine_dict = {}
                machine_dict["id"] = mach["id"]
                machine_dict["name"] = mach["name"]
                machine_dict["instance_id"] = mach["instance_id"]
                machine_dict["state"] = mach["state"]
                machine_dict["image"] = mach["config"]["image"]
            meter["machine"] = machine_dict

        if machine is True:
            meters = list(
                filter(
                    lambda m: m["machine"] is not None,
                    meters,
                )
            )

        if no_machine is True:
            meters = list(
                filter(
                    lambda m: m["machine"] is None,
                    meters,
                )
            )

        if machine_state is not None:
            meters = list(
                filter(
                    lambda m: m["machine"] is not None
                    and m["machine"]["state"] == machine_state,
                    meters,
                )
            )

        return meters

    def create(self, serial: str):
        meter = self._meter_by_serial(serial)

        machine_name = f"mediator-{serial}"
        machine_metadata = {"meter_id": meter["id"]}

        answer = input(f"""
Fly App:    {FLY_APP}
Image:      {SIMT_EMLITE_IMAGE}
Name:       {machine_name}
Metadata:   {machine_metadata}

Create machine with these details (y/n): """)
        if answer != "y":
            print("\naborting ...\n")
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
        print(f"machine {machine}")
        self.machines.stop(FLY_APP, machine["id"])
        return machine["id"], machine["instance_id"]

    # =================================
    #   Utils
    # =================================

    # TODO: these are duplicated in emop - put them in one tool or at least consolidate the duplicated code

    def env_show(self):
        print(config["env"])

    def env_set(self, env: str):
        allowed_env = ["prod", "qa", "local"]
        if env not in allowed_env:
            print(f"ERROR: env must be one of {allowed_env}")
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
            print(f"env set to {env}")
        else:
            print("failed to set env")

    def _machine_by_serial(self, serial):
        meter = self._meter_by_serial(serial)
        machines_match = list(filter(lambda m: m["id"] == meter["id"], self._list()))
        if len(machines_match) == 0:
            raise Exception(f"machine for meter {serial} not found")
        return machines_match[0]["machine"]

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
