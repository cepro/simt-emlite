import argparse
import random
import socket
import os
import sys
import postgrest

from httpx import ConnectError
from typing import Dict, List

from simt_emlite.orchestrate.adapter.base_adapter import ContainerState
from simt_emlite.orchestrate.adapter.docker_adapter import DockerAdapter
from simt_emlite.orchestrate.adapter.fly_adapter import FlyAdapter
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client


logger = get_logger(__name__, __file__)

mediator_image: str = os.environ.get("MEDIATOR_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")
site_code: str = os.environ.get("SITE")


class Mediators():
    def __init__(self, use_fly: bool):
        self.supabase = supa_client(
            supabase_url, supabase_key, flows_role_key)
        
        # TODO: look at config and the presense of the fly api key
        if use_fly:
            self.containers = FlyAdapter(mediator_image)
        else:
            self.containers = DockerAdapter(mediator_image)

    def start_one(self, meter_id: str) -> int:
        container_id = self.container_id_by_meter_id(meter_id)
        if (container_id is not None):
            logger.info('start existing container',
                        meter_id=meter_id, container_id=container_id)
            self.containers.start(container_id)

        ip_address = self._get_meter_ip(meter_id)
        mediator_port = self._allocate_mediator_listen_port()
        container_name = f"mediator-{ip_address}"

        logger.info("create and start new container",
                    container_name=container_name,
                    mediator_port=mediator_port,
                    ip_address=ip_address,
                    meter_id=meter_id)
        
        self.containers.create(
            "simt_emlite.mediator.grpc.server",
            container_name,
            meter_id, 
            ip_address,
            mediator_port
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
        ids = self._all_started_mediator_ids()
        for id in ids:
            logger.info("stopping container", container_id=id)
            self.containers.stop(id)

    def destroy_all(self):
        ids = self._all_mediator_ids(status=ContainerState.STOPPED)
        logger.info("found %s exited containers", len(ids))
        for id in ids:
            logger.info("removing container", container_id=id)
            self.containers.destroy(id)

    def stop_one(self, meter_id: str):
        id = self.container_id_by_meter_id(meter_id)
        if (id is None):
            logger.info(
                "stop_one: skip - container for meter already stopped", meter_id=meter_id)
            return

        logger.info(
            "stop_one stopping container", container_id=id, meter_id=meter_id)
        self.containers.stop(id)

    def container_id_by_meter_id(self, meter_id: str):
        containers = self.containers.list(("meter_id", meter_id))
        if (len(containers) == 0):
            return None
        return containers[0].id

    def _all_started_mediator_ids(self) -> List[str]:
        started_containers = self._all_mediator_ids(status=ContainerState.STARTED)
        logger.info("found %s started containers", len(started_containers))
        return list(map(lambda c: c.id, started_containers))
    
    def _all_mediator_ids(self, status: ContainerState = None) -> List[str]:
        containers = self.containers.list(status_filter=status)
        return list(map(lambda c: c.id, 
                list(filter(lambda c: c.name.startswith('mediator-'), containers))))

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
    parser.add_argument('--destroy-all', action='store_true', help='Remove all')
    args = parser.parse_args()

    try:
        mediators = Mediators()

        if args.start_one:
            mediators.start_one(args.start_one)
        elif args.start_all:
            mediators.start_all()
        elif args.stop_all:
            mediators.stop_all()
        elif args.destroy_all:
            mediators.destroy_all()
        else:
            parser.print_usage()

    except postgrest.exceptions.APIError as e:
        logger.error("start mediators failed", error=e.message)
    except Exception as e:
        logger.error("unknown failure in mediators", error=e)
