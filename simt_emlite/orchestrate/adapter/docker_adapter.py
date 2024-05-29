from typing import List

import fire

import docker
from simt_emlite.orchestrate.adapter.base_adapter import BaseAdapter, ContainerState
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

docker_status = {
    ContainerState.STARTED: "running",
    ContainerState.STOPPED: "exited",
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
    ) -> List[str]:
        filters = {"ancestor": "simt-emlite"}

        if metadata_filter is not None:
            filters["label"] = f"{metadata_filter[0]}={metadata_filter[1]}"

        if status_filter is not None:
            filters["status"] = docker_status[status_filter]

        containers = self.docker_client.containers.list(
            all=True,
            filters=filters,
        )
        container_ids = list(map(lambda c: c.id, containers))
        logger.info(container_ids)
        return container_ids

    def create(
        self, cmd: str, name: str, meter_id: str, ip_address: str, mediator_port: int
    ) -> str:
        envvar_dict = {"EMLITE_HOST": ip_address, "LISTEN_PORT": mediator_port}
        if self.use_socks is True:
            logger.info(
                "configuring socks proxy ", socks_host=self.socks_dict["SOCKS_HOST"]
            )
            envvar_dict.update(self.socks_dict)

        container = self.docker_client.containers.run(
            self.image,
            name=name,
            command=cmd,
            environment=envvar_dict,
            network_mode="host",
            restart_policy={"Name": "always"},
            labels={
                "meter_id": meter_id,
                "emlite_host": ip_address,
                "listen_port": str(mediator_port),
            },
            detach=True,
        )
        return container.id

    def start(self, id: str):
        container = self.docker_client.containers.get(id)
        container.start()

    def stop(self, id: str):
        container = self.docker_client.containers.get(id)
        container.stop()

    def destroy(self, id: str):
        container = self.docker_client.containers.get(id)
        container.kill()
        container.remove(force=True)


def main():
    fire.Fire(DockerAdapter)


if __name__ == "__main__":
    main()
