# mypy: disable-error-code="import-untyped"
import sys
from typing import List

import dns.resolver
from simt_fly_machines.api import API, FLY_REGION_DEFAULT

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
    ContainerState.STARTING: "starting",
    ContainerState.STOPPED: "stopped",
    ContainerState.STOPPING: "stopping",
    ContainerState.REMOVING: "destroying",
    ContainerState.CREATED: "created",
    ContainerState.FAILED: "failed",
}

CONTAINER_STATUS = {
    "started": ContainerState.STARTED,
    "stopped": ContainerState.STOPPED,
    "stopping": ContainerState.STOPPING,
    "starting": ContainerState.STARTING,
    "destroying": ContainerState.REMOVING,
    "created": ContainerState.CREATED,
    "failed": ContainerState.FAILED,
}


def metadata_filter_fn(key, value):
    def machine_filter(machine) -> bool:
        if "metadata" not in machine["config"]:
            return False
        metadata = machine["config"]["metadata"]
        return key in metadata and metadata[key] == value

    return machine_filter


class FlyAdapter(BaseAdapter):
    def __init__(
        self,
        api_token: str,
        dns_server: str,
        image: str,
        is_single_meter_app: bool = False,
        app_name: str | None = None,
        serial: str | None = None,
        use_private_address: bool | None = None,
        region: str | None = None
    ):
        super().__init__()
        self.api = API(api_token)
        self.dns_server = dns_server
        self.image = image
        self.is_single_meter_app = is_single_meter_app
        self.fly_app = app_name
        self.serial = serial
        self.region = region if region is not None else FLY_REGION_DEFAULT

        if is_single_meter_app and serial is None:
            raise Exception("FlyAdapter needs a serial to work with a single meter app")

        # default to public for single meter apps and private for everything else
        self.use_private_address = use_private_address
        if self.use_private_address is None:
            self.use_private_address = not self.is_single_meter_app

    def list(
        self,
        metadata_filter: tuple[str, str] | None = None,
        status_filter: ContainerState | None = None,
    ) -> List[Container]:
        machines = self.api.list(self.fly_app, region=self.region)

        if "error" in machines:
            logger.warning(f"failed to get machines {machines}", fly_app=self.fly_app)
            return []

        machines = list(filter(lambda m: m["name"].startswith("mediator-"), machines))

        # machines in an odd state will have no config - they are in the
        #   machines listing but don't really exist (have asked fly about this)
        machines = list(filter(lambda m: m["config"] is not None, machines))

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
        port: int | None = None,
        additional_internal_port: int | None = None,
        skip_confirm=False,
        use_cert_auth=False,
    ) -> str:
        machine_name = f"mediator-{serial}"
        metadata = self._metadata(meter_id, ip_address)

        # TODO: move this in to the CLI
        #       don't want interactions or sys.exit in this module
        if skip_confirm is not True:
            answer = input(f"""
Fly App:    {self.fly_app}
Region:     {self.region}
Image:      {self.image}
Name:       {machine_name}
Metadata:   {metadata}

Create machine with these details (y/n): """)
            if answer != "y":
                print("\naborting ...\n")
                sys.exit(1)

        create_response = self.api.create(
            self.fly_app,
            self.image,
            [cmd],
            port=port,
            additional_internal_port=additional_internal_port,
            name=machine_name,
            env_vars=self._env_vars(ip_address, use_cert_auth),
            metadata=metadata,
            extra_config={"region": self.region},
        )
        logger.info(f"create machine response {create_response}")

        if "error" in create_response:
            logger.error(f"create machine failed [{create_response['error']}]")
            sys.exit(1)

        logger.info(
            f"created machine with id {create_response['id']}",
            machine_id=create_response["id"],
        )
        return create_response["id"]

    def start(self, id: str) -> None:
        self.api.start(self.fly_app, id)

    def stop(self, id: str) -> None:
        self.api.stop(self.fly_app, id)

    def destroy(self, id: str, force: bool = False) -> None:
        if not force:
            stop_rsp = self.api.stop(self.fly_app, id)
            print(f"stop_rsp [{id}]: {stop_rsp}")

            machine = self.api.get(self.fly_app, id)
            wait_rsp = self.api.wait(
                self.fly_app,
                id,
                machine["instance_id"],
                FLY_STATUS[ContainerState.STOPPED],
            )
            print(f"wait_rsp [{id}]: {wait_rsp}")

        destroy_rsp = self.api.destroy(
            self.fly_app, id, force=force, region=self.region
        )
        print(f"destroy_rsp [{id}]: {destroy_rsp}")

    def mediator_address(self, meter_id: str, serial: str) -> str | None:
        machines = self.list(("meter_id", meter_id))
        if len(machines) == 0:
            print("no match")
            return None
        return self.get_app_address(machines[0])

    def get_app_address(self, machine) -> str:
        if self.use_private_address:
            if self.is_single_meter_app:
                return self.get_private_address_for_single_meter_app(machine)
            else:
                return self.get_private_address(machine)
        else:
            return self.get_public_address()

    # connect by public address. for single meter per app setup that supports
    # external access through fly proxy.
    def get_public_address(self):
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ["1.1.1.1"]
        try:
            answers = resolver.resolve(f"{self.fly_app}.fly.dev", "A")
            return f"{answers[0].address}:50051"
        except Exception as e:
            print(f"\nFailed to resolve address [{e}]\n")
            sys.exit(11)

    # connect by private address. assumes wireguard running and connects via ip
    # private to our fly organisation. see fly docs on flycast and private
    # '6PN' addresses.
    def get_private_address_for_single_meter_app(self, machine):
        mediator_host = self.get_private_flycast_ip()
        mediator_port = 44444  # fixed port for single_meter_app private access
        # ipv6 so wrap host ip in []'s
        return f"[{mediator_host}]:{mediator_port}"

    # connect by private address. assumes wireguard running and connects via ip
    # private to our fly organisation. see fly docs on flycast and private
    # '6PN' addresses.
    def get_private_address(self, machine):
        mediator_host = self.get_private_flycast_ip()
        mediator_port = machine.port
        # ipv6 so wrap host ip in []'s
        return f"[{mediator_host}]:{mediator_port}"

    def get_private_flycast_ip(self):
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [self.dns_server]
        try:
            answers = resolver.resolve(f"{self.fly_app}.flycast", "AAAA")
            return answers[0].address
        except Exception as e:
            print(f"\nFailed to resolve flycast address [{e}]\n")
            print("Has Wireguard been started??\n")
            sys.exit(10)
