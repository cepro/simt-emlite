from emlite_mediator.util.logging import get_logger

import argparse
import random
import socket
import docker
import os
import sys
import postgrest

from httpx import ConnectError
from typing import Dict, List

from emlite_mediator.util.supabase import supa_client


logger = get_logger(__name__, __file__)

mediator_image: str = os.environ.get("MEDIATOR_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")
site_code: str = os.environ.get("SITE")


class Mediators():
    def __init__(self):
        self.supabase = supa_client(
            supabase_url, supabase_key, flows_role_key)
        self.docker_client = docker.from_env()

    def start_one(self, meter_id: str) -> int:
        container = self.container_by_meter_id(meter_id)
        if (container is not None):
            logger.info('start existing container',
                        meter_id=meter_id, container_name=container.name)
            container.start()
            return container.labels['listen_port']

        ip_address = self._get_meter_ip(meter_id)
        mediator_port = self._allocate_mediator_listen_port()
        container_name = f"mediator-{ip_address}"

        logger.info("create and start new container",
                    container_name=container_name,
                    mediator_port=mediator_port,
                    ip_address=ip_address,
                    meter_id=meter_id)

        self.docker_client.containers.run(
            mediator_image,
            name=container_name,
            command="emlite_mediator.mediator.grpc.server",
            environment={
                "EMLITE_HOST": ip_address,
                "LISTEN_PORT": mediator_port
            },
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
        logger.info('start_many invoked', meter_ids=meter_ids)
        ports = {}
        for meter_id in meter_ids:
            ports['meter_id'] = self.start_one(meter_id)
        return ports

    def start_all(self) -> Dict[str, int]:
        try:
            sites = self.supabase.table('sites').select(
                'id').ilike('code', site_code).execute()
            site_id = list(sites.data)[0]['id']
            rows = (self.supabase.table('meter_registry')
                    .select('id')
                    .eq('site', site_id)

                    # only start mediators for active meters.
                    # a meter is active in a max of 1 env at a time.
                    # so in this way we ensure there is only ever 1 mediator
                    #   per physical meter
                    .eq('mode', 'active')

                    .execute())
        except ConnectError as e:
            logger.error("Supabase connection failure", error=e)
            sys.exit(10)
        ids = list(map(lambda row: row['id'], rows.data))
        return self.start_many(ids)

    def stop_all(self):
        mediator_containers = self._all_running_mediators()
        for mediator in mediator_containers:
            logger.info("stopping container", container_name=mediator.name)
            mediator.stop()

    def remove_all(self):
        containers = self._all_mediators(status="exited")
        logger.info("found %s exited containers", len(containers))
        for mediator in containers:
            logger.info("removing container", container_name=mediator.name)
            mediator.remove(force=True)

    def stop_one(self, meter_id: str):
        container = self.container_by_meter_id(meter_id)
        if (container == None):
            logger.info(
                "stop_one: skip - container for meter already stopped", meter_id=meter_id)
            return

        logger.info(
            "stop_one stopping container", container_name=container.name, meter_id=meter_id)
        container.stop(timeout=3)

    def container_by_meter_id(self, meter_id: str):
        containers = self.docker_client.containers.list(all=True,
                                                        filters={"label": f"meter_id={meter_id}"})
        if (len(containers) == 0):
            return None
        return containers[0]

    # mediator containers with either status 'running' and 'restarting
    def _all_running_mediators(self):
        running_containers = self._all_mediators(status="running")
        logger.info("found %s running containers", len(running_containers))
        restarting_containers = self._all_mediators(status="restarting")
        logger.info("found %s restarting containers",
                    len(restarting_containers))
        return running_containers + restarting_containers

    def _all_mediators(self, status=None):
        filters = {"status": status} if status else {}
        containers = self.docker_client.containers.list(all=True,
                                                        filters=filters)
        return list(filter(lambda c: c.name.startswith('mediator-'), containers))

    def _get_meter_ip(self, meter_id: str):
        meter_registry_record = None

        try:
            meter_registry_record = self.supabase.table('meter_registry').select(
                'ip_address').eq("id", meter_id).execute()
        except ConnectError as e:
            logger.error("Supabase connection failure", error=e)
            sys.exit(12)

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
    if not site_code:
        logger.error("SITE is not set")
        exit(3)

    parser = argparse.ArgumentParser()
    parser.add_argument('--start-one', metavar='<meter_id>')
    parser.add_argument('--start-all', action='store_true', help='Start all')
    parser.add_argument('--stop-all', action='store_true', help='Stop all')
    parser.add_argument('--remove-all', action='store_true', help='Remove all')
    args = parser.parse_args()

    try:
        mediators = Mediators()

        if args.start_one:
            mediators.start_one(args.start_one)
        elif args.start_all:
            mediators.start_all()
        elif args.stop_all:
            mediators.stop_all()
        elif args.remove_all:
            mediators.remove_all()
        else:
            parser.print_usage()

    except postgrest.exceptions.APIError as e:
        logger.error("start mediators failed", error=e.message)
    except Exception as e:
        logger.error("unknown failure in mediators", error=e)
