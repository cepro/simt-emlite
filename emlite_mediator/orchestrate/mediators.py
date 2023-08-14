
import random
import socket
import docker
import os
import sys

from httpx import ConnectError
from typing import Dict, List
from supabase import create_client, Client

from emlite_mediator.util.logging import get_logger

logger = get_logger('mediators')

# Initially this handful of meters are the only ones running a mediator all
# the time. The following are the emnify id's of all the WLCE devices
# tagged 'Landlord'.
# Later all meters will run a mediator all the time
ALWAYS_UP_EMNIFY_IDS = [
    12585053,  # Plot 18-19.C
    12108323,  # Plot 18-19.G (3 phase)
    9651015,   # Plot 24-25.C
    12585039,  # Plot 24-25.G (3 phase)
]

mediator_image: str = os.environ.get("MEDIATOR_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")


class Mediators():
    supabase: Client
    docker_client: docker.DockerClient

    def __init__(self):
        self.supabase = create_client(supabase_url, supabase_key)
        self.docker_client = docker.from_env()

    def start_one(self, meter_id: str) -> int:
        ip_address = self._get_meter_ip(meter_id)
        mediator_port = self._allocate_mediator_listen_port()

        env_vars = {
            "EMLITE_HOST": ip_address,
            "LISTEN_PORT": mediator_port
        }

        logger.info("create mediator [listen=%s, ip=%s, id=%s]",
                    mediator_port, ip_address, meter_id)

        self.docker_client.containers.run(
            mediator_image,
            command="emlite_mediator.mediator.grpc.server",
            environment=env_vars,
            network_mode="host",
            restart_policy={"Name": "always"},
            labels={
                "meter_id": meter_id,
                "emlite_host": ip_address,
                "listen_port": str(mediator_port)
            },
            detach=True
        )

        return mediator_port

    def start_many(self, meter_ids: List[str]) -> Dict[str, int]:
        logger.info('start_many: ids [%s]', meter_ids)
        ports = {}
        for meter_id in meter_ids:
            ports['meter_id'] = self.start_one(meter_id)
        return ports

    def start_many_by_emnify_id(self, emnify_ids: List[str]) -> Dict[str, int]:
        rows = self.supabase.table('meter_registry').select(
            'id').in_("emnify_id", emnify_ids).execute()
        ids = list(map(lambda row: row['id'], rows.data))
        return self.start_many(ids)

    def stop_one(self, meter_id: str):
        containers = self.docker_client.containers.list(
            filters={"label": f"meter_id={meter_id}"})
        if (len(containers) == 0):
            logger.info(
                "stop_one: skip - container for meter [%s] already stopped", meter_id)
            return

        container = containers[0]
        logger.info(
            "stop_one stopping container [%s] for meter_id [%s]", container.name, meter_id)
        container.stop()

    def _get_meter_ip(self, meter_id: str):
        meter_registry_record = None

        try:
            meter_registry_record = self.supabase.table('meter_registry').select(
                'ip_address').eq("id", meter_id).execute()
        except ConnectError as e:
            logger.error("Supabase connection failure [%s]", e)
            sys.exit(2)

        return meter_registry_record.data[0]['ip_address']

    def _allocate_mediator_listen_port(self) -> int:
        while True:
            port = random.randint(51000, 52000)
            if (not self._is_port_in_use(port)):
                return port

    def _is_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return False
            except socket.error:
                return True


if __name__ == '__main__':

    if not mediator_image:
        logger.error("MEDIATOR_IMAGE not set to a docker image.")
        exit(1)
    if not supabase_url or not supabase_key:
        logger.error(
            "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        exit(2)

    mediators = Mediators()
    mediators.start_many_by_emnify_id(ALWAYS_UP_EMNIFY_IDS)
