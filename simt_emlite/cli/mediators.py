import os
import subprocess
import sys
from datetime import datetime
from json import dumps
from typing import Dict, List, Union

import fire
from rich import box
from rich.console import Console
from rich.table import Table

from simt_emlite.orchestrate.adapter.container import ContainerState
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config
from simt_emlite.util.supabase import Client, supa_client

config = load_config()

SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
SUPABASE_ANON_KEY = config["supabase_anon_key"]
SUPABASE_URL = config["supabase_url"]

FLY_API_TOKEN = config["fly_token"]

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
        self.supabase: Client = supa_client(
            SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_ACCESS_TOKEN
        )

    def list(
        self,
        esco: str = None,
        mediator_state: Union[ContainerState] = None,
        mediator_exists: bool = None,
        json=False,
        show_all=False,
    ) -> List:
        """
        List meters and corresponding machines

        Args:
            esco: esco code [eg. 'hmce' for Hazelmead]
            mediator_state: one of [started, stopped, suspended, destroyed]
            mediator_exists: show only with or without mediators (ignore if not set)
            show_all: show all meters [True | False]
        """
        meters = self._list(
            esco=esco,
            mediator_state=mediator_state,
            mediator_exists=mediator_exists,
            show_all=show_all,
        )

        if json is True:
            print(dumps(meters, indent=2))
            return

        table = Table(
            "esco", "serial", "container state", "container image", box=box.SQUARE
        )

        for meter in meters:
            row_values = [meter["esco"], meter["serial"]]
            if meter["container"] is not None:
                row_values.append(meter["container"].status.name)
                row_values.append(meter["container"].image)
            table.add_row(*row_values)

        console = Console()
        console.print(table)

    def _list(
        self,
        esco: str = None,
        mediator_state: Union[ContainerState] = None,
        mediator_exists: bool = None,
        show_all=False,
    ) -> List:
        meters = self._get_meters(esco)

        # add container info
        escos = set(map(lambda m: m["esco"].lower(), meters))

        for esco_code in escos:
            containers_api = get_instance(esco_code)
            containers = containers_api.list()

            esco_meters = list(filter(lambda m: m["esco"] == esco_code, meters))

            for meter in esco_meters:
                container_matches = list(
                    filter(
                        lambda c: c.metadata["meter_id"] == meter["id"],
                        containers,
                    )
                )
                meter["container"] = (
                    container_matches[0] if len(container_matches) != 0 else None
                )

        if mediator_exists is not None:
            meters = list(
                filter(
                    lambda m: (mediator_exists is True and m["container"] is not None)
                    or (mediator_exists is False and m["container"] is None),
                    meters,
                )
            )

        if mediator_state is not None:
            meters = list(
                filter(
                    lambda m: m["container"] is not None
                    and m["container"].state == mediator_state,
                    meters,
                )
            )

        return meters

    def create(self, serial: str):
        meter = self._meter_by_serial(serial)

        fly_app = f"mediators-{meter["esco"]}"
        machine_name = f"mediator-{serial}"
        machine_metadata = {"meter_id": meter["id"]}

        answer = input(f"""
Fly App:    {fly_app}
Image:      {SIMT_EMLITE_IMAGE}
Name:       {machine_name}
Metadata:   {machine_metadata}

Create machine with these details (y/n): """)
        if answer != "y":
            print("\naborting ...\n")
            sys.exit(1)

        result = self.machines.create(
            fly_app,
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
        containers_api, container = self._container_by_serial(serial)
        containers_api.start(container.id)
        print("container started")

    def wait_one(self, serial: str, state: ContainerState):
        containers_api, container = self._container_by_serial(serial)
        return containers_api.wait(container.id, state)

    def destroy_one(self, serial: str):
        containers_api, container = self._container_by_serial(serial)
        return containers_api.destroy(container.id)

    def stop_one(self, serial: str) -> str:
        containers_api, container = self._container_by_serial(serial)
        containers_api.stop(container.id)
        print("container stopped")

    def start_many(self, meter_ids: List[str]) -> Dict[str, int]:
        pass

    def start_all(self) -> Dict[str, int]:
        pass

    def stop_all(self):
        pass

    def destroy_all(self):
        pass

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

    def _meter_by_serial(self, serial) -> str:
        meter_result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address,esco")
            .eq("serial", serial)
            .execute()
        )
        if len(meter_result.data) == 0:
            print(f"meter {serial} not found")
            sys.exit(10)

        meter = meter_result.data[0]

        esco_result = (
            self.supabase.table("escos")
            .select("code")
            .eq("id", meter["esco"])
            .execute()
        )
        meter["esco"] = esco_result.data[0]["code"]

        return meter

    def _get_meters(self, esco: str = None):
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

        return meters

    def _container_by_serial(self, serial: str):
        meter = self._meter_by_serial(serial)

        containers_api = get_instance(meter["esco"])
        container = containers_api.get(meter["id"])
        if container is None:
            print(f"No mediator found for serial {serial}")
            sys.exit(1)

        return containers_api, container


def main():
    fire.Fire(MediatorsCLI)


if __name__ == "__main__":
    main()
