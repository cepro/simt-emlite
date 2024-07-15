import sys
from typing import List

import dns.resolver
import fire
from simt_fly_machines.api import API

from simt_emlite.orchestrate.adapter.base_adapter import BaseAdapter
from simt_emlite.orchestrate.adapter.container import (
    Container,
    ContainerEnvironment,
    ContainerState,
)
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

FLY_STATUS = {
    ContainerState.STARTED: "started",
    ContainerState.STOPPED: "stopped",
    ContainerState.STOPPING: "stopping",
}

CONTAINER_STATUS = {
    "started": ContainerState.STARTED,
    "stopped": ContainerState.STOPPED,
    "stopping": ContainerState.STOPPING,
}


def metadata_filter_fn(key, value):
    def machine_filter(machine) -> bool:
        metadata = machine["config"]["metadata"]
        return key in metadata and metadata[key] == value

    return machine_filter


class FlyAdapter(BaseAdapter):
    def __init__(
        self,
        api_token: str,
        image: str,
        esco: str,
    ):
        super().__init__()
        self.api = API(api_token)
        self.esco = esco
        self.fly_app = f"mediators-{esco}"
        self.image = image

    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None,
    ) -> List[Container]:
        machines = self.api.list(self.fly_app)

        if metadata_filter:
            logger.debug(f"metadata filter [{metadata_filter}]")
            machines = list(
                filter(
                    metadata_filter_fn(metadata_filter[0], metadata_filter[1]), machines
                )
            )

        if status_filter:
            logger.debug(f"status filter [{status_filter}]")
            fly_state = FLY_STATUS[status_filter]
            machines = list(filter(lambda m: m["state"] == fly_state, machines))

        return list(
            map(
                lambda m: Container(
                    id=m["id"],
                    name=m["name"],
                    image=m["config"]["image"],
                    port=m["config"]["services"][0]["ports"][0]["port"],
                    status=CONTAINER_STATUS[m["state"]],
                    container_environment=ContainerEnvironment.FLY,
                    metadata=m["config"]["metadata"],
                ),
                machines,
            )
        )

    def create(
        self,
        cmd: str,
        meter_id: str,
        serial: str,
        ip_address: str,
    ) -> str:
        machine_name = f"mediator-{serial}"
        metadata = self._metadata(meter_id, ip_address)

        answer = input(f"""
Fly App:    {self.fly_app}
Image:      {self.image}
Name:       {machine_name}
Metadata:   {metadata}

Create machine with these details (y/n): """)
        if answer != "y":
            print("\naborting ...\n")
            sys.exit(1)

        machine = self.api.create(
            self.fly_app,
            self.image,
            [cmd],
            name=machine_name,
            env_vars=self._env_vars(ip_address),
            metadata=metadata,
        )
        logger.info(
            f"created machine with id {machine["id"]}", machine_id=machine["id"]
        )
        return machine["id"]

    def start(self, id: str):
        return self.api.start(self.fly_app, id)

    def stop(self, id: str):
        return self.api.stop(self.fly_app, id)

    def destroy(self, id: str):
        stop_rsp = self.api.stop(self.fly_app, id)
        print(f"stop_rsp {stop_rsp}")

        machine = self.api.get(self.fly_app, id)
        wait_rsp = self.api.wait(
            self.fly_app, id, machine["instance_id"], FLY_STATUS[ContainerState.STOPPED]
        )
        print(f"wait_rsp {wait_rsp}")

        destroy_rsp = self.api.destroy(self.fly_app, id)
        print(f"destroy_rsp {destroy_rsp}")

    def mediator_address(self, meter_id: str, serial: str):
        machines = self.list(("meter_id", meter_id))
        if len(machines) == 0:
            return None

        mediator_host = self.get_app_ip(self.esco)
        mediator_port = machines[0].port

        # ipv6 so wrap host ip in []'s
        return f"[{mediator_host}]:{mediator_port}"

    def get_app_ip(self, esco: str):
        resolver = dns.resolver.Resolver(configure=False)
        # cepro org dns server
        resolver.nameservers = [
            # "fdaa:5:3015::3",  # Cepro org DNS in Wireguard
            "fdaa::3",  # Fly.io DNS in machines
        ]
        try:
            answers = resolver.resolve(f"mediators-{esco}.flycast", "AAAA")
            return answers[0].address
        except Exception as e:
            print(f"Failed to resolve flycast address [{e}]")
            raise e


def main():
    fire.Fire(FlyAdapter)


if __name__ == "__main__":
    main()
