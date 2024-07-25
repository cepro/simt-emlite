from typing import List

import docker
from simt_emlite.orchestrate.adapter.base_adapter import BaseAdapter
from simt_emlite.orchestrate.adapter.container import (
    Container,
    ContainerEnvironment,
    ContainerState,
)
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

DOCKER_STATUS = {
    ContainerState.STARTED: "running",
    ContainerState.STOPPED: "exited",
    ContainerState.STOPPING: "stopping",
}

CONTAINER_STATUS = {
    "running": ContainerState.STARTED,
    "exited": ContainerState.STOPPED,
    "stopping": ContainerState.STOPPING,
}


class DockerAdapter(BaseAdapter):
    def __init__(self, image: str):
        super().__init__()

        self.docker_client = docker.from_env()
        self.image = image

    def list(
        self,
        metadata_filter: tuple[str, str] = None,
        status_filter: ContainerState = None,
    ) -> List[Container]:
        filters = {"ancestor": "simt-emlite"}

        if metadata_filter is not None:
            filters["label"] = f"{metadata_filter[0]}={metadata_filter[1]}"

        if status_filter is not None:
            filters["status"] = DOCKER_STATUS[status_filter]

        docker_containers = self.docker_client.containers.list(
            all=True,
            filters=filters,
        )

        return list(
            map(
                lambda c: Container(
                    id=c.id,
                    name=c.name,
                    image=c.image.tags[0],
                    status=CONTAINER_STATUS[c.status],
                    container_environment=ContainerEnvironment.DOCKER,
                    metadata=c.labels,
                ),
                docker_containers,
            )
        )

    def create(self, cmd: str, meter_id: str, serial: str, ip_address: str) -> str:
        mediator_name = f"mediator-{serial}"
        container = self.docker_client.containers.run(
            self.image,
            name=mediator_name,
            command=cmd,
            environment=self._env_vars(ip_address),
            network_mode="host",
            restart_policy={"Name": "always"},
            labels=self._metadata(meter_id, ip_address),
            detach=True,
        )
        return container.id

    def start(self, id: str):
        container = self.docker_client.containers.get(id)
        container.start()

    def stop(self, id: str):
        container = self.docker_client.containers.get(id)
        # stop is slow - 15 sec timeout before sending SIGINT
        # killing causes an immediate stop and this is fine for mediators
        container.kill()

    def destroy(self, id: str):
        container = self.docker_client.containers.get(id)
        container.kill()
        container.remove(force=True)

    def mediator_address(self, meter_id: str, serial: str):
        return "172.19.0.5:50051"
        # return f"mediator-{serial}:50051"
