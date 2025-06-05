import argparse
import concurrent.futures
import importlib
import logging
import sys
from datetime import datetime
from json import dumps
from typing import Dict, List, Union

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from simt_emlite.orchestrate.adapter.container import ContainerState
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config, set_config
from simt_emlite.util.meters import is_three_phase
from simt_emlite.util.supabase import Client, supa_client

config = load_config()

SUPABASE_ACCESS_TOKEN = config["supabase_access_token"]
SUPABASE_ANON_KEY = config["supabase_anon_key"]
SUPABASE_URL = config["supabase_url"]

FLY_API_TOKEN = config["fly_api_token"]

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


def rich_status_circle(color):
    return f"[{color}]●[/{color}]"


def rich_signal_circle(csq: int):
    if csq is None or csq < 1:
        color = "rgb(255,0,0)"  # Red
    elif csq > 22:
        color = "rgb(0,255,0)"  # Green
    elif csq > 17:
        color = "rgb(128,255,0)"  # Light Green
    elif csq > 12:
        color = "rgb(255,255,0)"  # Yellow
    elif csq > 7:
        color = "rgb(255,192,0)"  # Orange-yellow
    elif csq > 0:
        color = "rgb(255,128,0)"  # Orange
    return Text("●", style=color)


class MediatorsCLI:
    def __init__(self):
        self.supabase: Client = supa_client(
            SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_ACCESS_TOKEN
        )

    def list(
        self,
        esco: str = None,
        feeder: str = None,
        state: str = None,
        exists: bool = None,
        three_phase_only=False,
        json=False,
        show_all=False,
    ) -> List:
        container_state: Union[ContainerState] = (
            ContainerState.__members__[state.upper()] if state is not None else None
        )

        meters = self._list(
            esco=esco,
            feeder=feeder,
            state=container_state,
            exists=exists,
            three_phase_only=three_phase_only,
            show_all=show_all,
        )

        if json is True:
            print(dumps(meters, indent=2))
            return

        table = Table(
            "esco",
            "serial",
            "name",
            "signal",
            "health",
            "hardware",
            "feeder",
            # "container state",
            "version",
            "container id",
            box=box.SQUARE,
        )

        for meter in meters:
            row_values = [
                meter["esco"],
                meter["serial"],
                meter["name"],
                rich_signal_circle(meter["csq"]),
                rich_status_circle("green" if meter["health"] == "healthy" else "red"),
                meter["hardware"],
                meter["feeder"],
            ]
            if meter["container"] is not None:
                # row_values.append(meter["container"].status.name)
                row_values.append(
                    meter["container"].image.replace("registry.fly.io/simt-emlite:", "")
                )
                row_values.append(meter["container"].id)
            table.add_row(*row_values)

        console = Console()
        console.print(table)

    def _list(
        self,
        esco: str = None,
        feeder: str = None,
        state: Union[ContainerState] = None,
        exists: bool = None,
        three_phase_only=False,
        show_all=False,
    ) -> List:
        meters = self._get_meters(esco, feeder)

        if three_phase_only is True:
            meters = list(filter(lambda m: is_three_phase(m["hardware"]), meters))

        # add container info
        self._add_container_info_to_app_per_esco_meters(meters)
        self._add_container_info_to_app_per_serial_meters(meters)

        if exists is not None:
            meters = list(
                filter(
                    lambda m: (exists is True and m["container"] is not None)
                    or (exists is False and m["container"] is None),
                    meters,
                )
            )

        if state is not None:
            meters = list(
                filter(
                    lambda m: m["container"] is not None
                    and m["container"].status == state,
                    meters,
                )
            )

        return meters

    def create(self, serial: str, skip_confirm=False):
        meter = self._meter_by_serial(serial)

        # single meter per app always listen on default
        # None means a random port will be allocated
        internal_port = 50051 if meter["single_meter_app"] else None

        containers_api = get_instance(
            is_single_meter_app=meter["single_meter_app"],
            esco=meter["esco"],
            serial=serial,
        )
        result = containers_api.create(
            "simt_emlite.mediator.grpc.server",
            meter["id"],
            serial,
            meter["ip_address"],
            port=internal_port,
            skip_confirm=skip_confirm,
            use_cert_auth=meter["single_meter_app"],
        )
        return result

    def create_all(self, esco: str):
        if esco is None:
            print("esco mandatory")
            sys.exit(1)

        mediators = self._list(esco=esco, exists=False)

        answer = input(f"""Found {len(mediators)} mediators to create in ESCO {esco}.

Go ahead and create ALL of these? (y/n): """)
        if answer != "y":
            print("\naborting ...\n")
            sys.exit(1)

        for m in mediators:
            self.create(m["serial"], skip_confirm=True)

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

    def destroy_all(self, esco: str):
        if esco is None:
            print("esco mandatory")
            sys.exit(1)

        mediators = self._list(esco=esco, exists=True)

        answer = input(f"""Found {len(mediators)} mediators to destroy in ESCO {esco}.

Go ahead and destroy ALL of these? (y/n): """)
        if answer != "y":
            print("\naborting ...\n")
            sys.exit(1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(self.destroy_one, m["serial"]) for m in mediators
            ]
        concurrent.futures.wait(futures)

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

    # =================================
    #   Utils
    # =================================

    # TODO: these are duplicated in emop - put them in one tool or at least consolidate the duplicated code

    def version(self):
        version = importlib.metadata.version("simt-emlite")
        logging.info(version)

    def env_show(self):
        logging.info(config["env"])

    def env_set(self, env: str):
        allowed_env = ["prod", "qa", "local"]
        if env not in allowed_env:
            logging.info(f"ERROR: env must be one of {allowed_env}")
            sys.exit(1)
        set_config(env)
        logging.info(f"env set to {env}")

    def _machine_by_serial(self, serial):
        meter = self._meter_by_serial(serial)
        machines_match = list(filter(lambda m: m["id"] == meter["id"], self._list()))
        if len(machines_match) == 0:
            raise Exception(f"machine for meter {serial} not found")
        return machines_match[0]["machine"]

    def _meter_by_serial(self, serial) -> str:
        meter_result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address,esco,single_meter_app")
            .eq("serial", serial)
            .execute()
        )
        if len(meter_result.data) == 0:
            print(f"meter {serial} not found")
            sys.exit(10)

        meter = meter_result.data[0]

        if meter["esco"] is not None:
            esco_result = (
                self.supabase.table("escos")
                .select("code")
                .eq("id", meter["esco"])
                .execute()
            )
            meter["esco"] = esco_result.data[0]["code"]

        return meter

    def _get_meters(self, esco: str = None, feeder: str = None):
        meters_result = self.supabase.rpc(
            "get_meters_for_cli", {"esco_filter": esco, "feeder_filter": feeder}
        ).execute()
        return meters_result.data

    def _container_by_serial(self, serial: str):
        meter = self._meter_by_serial(serial)

        containers_api = get_instance(
            is_single_meter_app=meter["single_meter_app"],
            esco=meter["esco"],
            serial=serial,
        )
        container = containers_api.get(meter["id"])
        if container is None:
            print(f"No mediator found for serial {serial}")
            sys.exit(1)

        return containers_api, container

    def _add_container_info_to_app_per_esco_meters(self, meters):
        escos = set(
            map(
                lambda m: m["esco"].lower(),
                list(filter(lambda m: m["esco"] is not None, meters)),
            )
        )

        # we get info an 'app' at a time because fly machines api works per app
        # not across apps. there for first add info to all per-esco apps then
        # any per-serial apps (single meter per app)
        for esco_code in escos:
            containers_api = get_instance(esco=esco_code)
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

    def _add_container_info_to_app_per_serial_meters(self, meters):
        single_app_meters = list(filter(lambda m: m["esco"] is None, meters))
        for meter in single_app_meters:
            containers_api = get_instance(serial=meter["serial"])
            containers = containers_api.list()
            container_matches = list(
                filter(
                    lambda c: c.metadata["meter_id"] == meter["id"],
                    containers,
                )
            )
            meter["container"] = (
                container_matches[0] if len(container_matches) != 0 else None
            )


ESCO_FILTER_HELP = "Filter by ESCO code [eg. wlce, hmce, lab]"


def main():
    logging.basicConfig(level=logging.INFO)
    # supress supabase py request logging:
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser")

    subparsers.add_parser("version", help="Show version")

    subparsers.add_parser("env_show", help="Show current environment context")
    subparsers.add_parser(
        "env_set",
        help="Set CLI environment context [points ~/.simt/emlite.env at ~/.simt/emlite.<env>.env]",
    ).add_argument(
        "env",
        choices=["prod", "qa", "local"],
    )

    parser_list = subparsers.add_parser(
        "list",
        help="List meters and mediators details",
    )
    parser_list.add_argument("-e", "--esco", help=ESCO_FILTER_HELP)
    parser_list.add_argument(
        "--exists",
        action=argparse.BooleanOptionalAction,
        help="Filter by existance of mediator for each meter.",
    )
    parser_list.add_argument(
        "--three_phase_only",
        action=argparse.BooleanOptionalAction,
        help="Filter for three phase meters.",
    )
    parser_list.add_argument(
        "-f", "--feeder", help="Filter by name of feeder the meter is on"
    )

    # Broken as Container does not yet serialise:
    #
    # parser_list.add_argument(
    #     "--json",
    #     action="store_true",
    #     help="Output result in JSON ",
    # )
    parser_list.add_argument(
        "-s",
        "--state",
        help="Filter by mediator state",
        choices=[
            ContainerState.STARTED.name.lower(),
            ContainerState.STOPPED.name.lower(),
            ContainerState.STOPPING.name.lower(),
            ContainerState.FAILED.name.lower(),
        ],
    )

    parser_create = subparsers.add_parser(
        "create",
        help="Create mediator for given meter serial",
    )
    parser_create.add_argument("serial")
    parser_create.add_argument(
        "--skip_confirm",
        action=argparse.BooleanOptionalAction,
        help="Skip interactive confirmation",
    )

    parser_create_all = subparsers.add_parser(
        "create_all",
        help="Create all mediators for a given ESCO",
    )
    parser_create_all.add_argument("esco", help=ESCO_FILTER_HELP)

    subparsers.add_parser(
        "destroy_one",
        help="Destroy a mediator for given meter serial",
    ).add_argument("serial")

    subparsers.add_parser(
        "destroy_all",
        help="Destroy all mediators for a given ESCO",
    ).add_argument("esco", help=ESCO_FILTER_HELP)

    kwargs = vars(parser.parse_args())

    command = kwargs.pop("subparser")
    if command is None:
        parser.print_help()
        exit(-1)

    # logging.info(kwargs)

    cli = MediatorsCLI()
    method = getattr(cli, command)
    method(**kwargs)


if __name__ == "__main__":
    main()
