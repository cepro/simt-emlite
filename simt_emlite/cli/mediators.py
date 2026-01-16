import argparse
import importlib
import logging
import os
import sys
from datetime import datetime
from json import dumps
from typing import Any, Dict, List, cast

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from supabase import Client as SupabaseClient

from simt_emlite.jobs.meter_sync import MeterSyncJob
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.util.config import load_config, set_config
from simt_emlite.util.meters import is_three_phase
from simt_emlite.util.supabase import as_first_item, as_list, supa_client

config = load_config()

SUPABASE_ACCESS_TOKEN: str | int | None = config["supabase_access_token"]
SUPABASE_ANON_KEY: str | int | None = config["supabase_anon_key"]
SUPABASE_URL: str | int | None = config["supabase_url"]

FLY_REGION: str | None = cast(str | None, config["fly_region"])
ENV: str | int | None = config["env"]



"""
    This is a CLI for managing Emlite mediator processes.
"""

LOG_TIMES = False


def log(msg: str) -> None:
    if LOG_TIMES:
        print(f"{datetime.now().strftime('%S.%f')} {msg}")


def rich_status_circle(color: str) -> str:
    return f"[{color}]●[/{color}]"


def rich_signal_circle(csq: int | None) -> Text:
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
    def __init__(self) -> None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise Exception("SUPABASE_URL and SUPABASE_ANON_KEY not set")

        self.supabase: SupabaseClient = supa_client(
            str(SUPABASE_URL), str(SUPABASE_ANON_KEY), str(SUPABASE_ACCESS_TOKEN)
        )

    def list(
        self,
        esco: str | None = None,
        feeder: str | None = None,
        three_phase_only: bool = False,
        json: bool = False,
    ) -> None:
        meters = self._list(
            esco=esco,
            feeder=feeder,
            three_phase_only=three_phase_only,
        )

        if json is True:
            print(dumps(meters, indent=2))
            return None

        table = Table(
            "esco",
            "serial",
            "name",
            "signal",
            "health",
            "hardware",
            "feeder",
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
            table.add_row(*row_values)

        console = Console()
        console.print(table)

    def _list(
        self,
        esco: str | None = None,
        feeder: str | None = None,
        three_phase_only: bool = False,
    ) -> List:
        meters = self._get_meters(esco, feeder)

        if three_phase_only is True:
            meters = list(filter(lambda m: is_three_phase(m["hardware"]), meters))

        return meters

    def sync(self, serial: str) -> None:
        """Run sync jobs for a specific meter by serial number."""
        meter = self._meter_by_serial(serial)

        # Get the mediator address for this meter
        containers_api = get_instance(
            is_single_meter_app=meter["single_meter_app"],
            esco=meter["esco"],
            serial=serial,
            region=FLY_REGION,
            env=cast(str | None, ENV),
        )

        mediator_address = containers_api.mediator_address(meter["id"], serial)
        if mediator_address is None:
            print(f"No mediator container exists for meter {serial}")
            sys.exit(1)

        # Get required environment variables
        supabase_url = os.environ.get("SUPABASE_URL") or str(SUPABASE_URL)
        supabase_key = os.environ.get("SUPABASE_ANON_KEY") or str(SUPABASE_ANON_KEY)
        flows_role_key = os.environ.get("FLOWS_ROLE_KEY") or str(SUPABASE_ACCESS_TOKEN)

        if not supabase_url or not supabase_key or not flows_role_key:
            print(
                "Missing required environment variables: SUPABASE_URL, SUPABASE_ANON_KEY, FLOWS_ROLE_KEY"
            )
            sys.exit(1)

        for frequency in ["daily", "hourly", "12hourly"]:
            print(
                f"Syncing meter {serial} at {mediator_address} with syncers at frequency {frequency} [see flows.meter_metrics]\n"
            )

            # Create and run the sync job
            job = MeterSyncJob(
                meter_id=meter["id"],
                mediator_address=mediator_address,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                flows_role_key=flows_role_key,
                run_frequency=frequency,
            )

            try:
                job.sync()
                print(f"\nSync completed successfully for meter {serial}\n")
            except Exception as e:
                print(f"Sync failed for meter {serial}: {e}")
                sys.exit(1)

    # =================================
    #   Utils
    # =================================

    # TODO: these are duplicated in emop - put them in one tool or at least consolidate the duplicated code

    def version(self) -> None:
        version = importlib.metadata.version("simt-emlite")
        logging.info(version)

    def env_show(self) -> None:
        logging.info(config["env"])

    def env_set(self, env: str) -> None:
        try:
            set_config(env)
            logging.info(f"env set to {env}")
        except Exception as e:
            logging.error(f"ERROR: {e}")
            sys.exit(1)

    def _meter_by_serial(self, serial) -> Dict[str, Any]:
        meter_result = (
            self.supabase.table("meter_registry")
            .select("id,ip_address,esco,single_meter_app")
            .eq("serial", serial)
            .execute()
        )
        if len(as_list(meter_result)) == 0:
            print(f"meter {serial} not found")
            sys.exit(10)

        meter = as_first_item(meter_result)

        if meter["esco"] is not None:
            esco_result = (
                self.supabase.table("escos")
                .select("code")
                .eq("id", meter["esco"])
                .execute()
            )
            meter["esco"] = as_first_item(esco_result)["code"]

        return meter

    def _get_meters(self, esco: str | None = None, feeder: str | None = None):
        meters_result = self.supabase.rpc(
            "get_meters_for_cli", {"esco_filter": esco, "feeder_filter": feeder}
        ).execute()
        return as_list(meters_result)


ESCO_FILTER_HELP = "Filter by ESCO code [eg. wlce, hmce, lab]"


def main() -> None:
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
    ).add_argument("env")

    parser_list = subparsers.add_parser(
        "list",
        help="List meters details",
    )
    parser_list.add_argument("-e", "--esco", help=ESCO_FILTER_HELP)
    parser_list.add_argument(
        "--three_phase_only",
        action=argparse.BooleanOptionalAction,
        help="Filter for three phase meters.",
    )
    parser_list.add_argument(
        "-f", "--feeder", help="Filter by name of feeder the meter is on"
    )

    parser_sync = subparsers.add_parser(
        "sync",
        help="Run sync jobs for a specific meter by serial number",
    )
    parser_sync.add_argument("serial", help="Serial number of the meter to sync")

    kwargs = vars(parser.parse_args())

    command = kwargs.pop("subparser")
    if command is None:
        parser.print_help()
        exit(-1)

    # logging.info(kwargs)

    try:
        cli = MediatorsCLI()
        method = getattr(cli, command)
        method(**kwargs)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: Operation cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
