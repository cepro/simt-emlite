from emlite_mediator.util.logging import get_logger

import docker
import os
import sys
import time

from emlite_mediator.orchestrate.mediators import Mediators
from typing import Any, Callable

from emlite_mediator.util.supabase import supa_client, Client

logger = get_logger(__name__, __file__)

mediator_image: str = os.environ.get("MEDIATOR_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")


def filter_connected(meter): return meter['ip_address'] is not None


"""
    This script is a base class for scripts that run a job for all meters.

    Memory is limited so we chunk runs - 5 at a time for now.

    TODO: soon replace this way of invoking a script in a container per meter
    to have a single script that runs for all meters.
"""


class RunJobForAllMeters():
    job_name: str
    filter_fn: Callable[[Any], bool]

    supabase: Client
    docker_client: docker.DockerClient

    def __init__(self, job_name: str, filter_fn=None):
        self._check_environment()
        self.job_name = job_name
        self.filter_fn = filter_fn
        self.supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.docker_client = docker.from_env()
        self.mediators = Mediators()

        global logger
        logger = logger.bind(job_name=job_name, mediator_image=mediator_image)

    def run(self):
        logger.info("starting ...")

        registry_result = self.supabase.table(
            'meter_registry').select('id,ip_address,serial,hardware').order(column='serial').execute()
        if (len(registry_result.data) == 0):
            logger.error("no meters record found")
            sys.exit(11)

        meters = list(filter(filter_connected, registry_result.data))
        if (self.filter_fn):
            meters = list(filter(self.filter_fn, meters))

        # process meter runs in chunks of chunk_size to avoid
        # running out of memory from starting mediators
        chunk_size = 5
        num_chunks = (len(meters) // chunk_size) + 1
        for chunk_idx in list(range(0, num_chunks)):
            range_start = chunk_idx * chunk_size
            range_end = range_start + chunk_size

            chunk_meters = meters[range_start:range_end]

            for meter in chunk_meters:
                logger.info(
                    "next meter - check mediator container exists",
                    meter_id=meter['id']
                )

                mediator_container = self.mediators.container_by_meter_id(
                    meter['id'])
                if (mediator_container == None):
                    logger.error(
                        "NO MEDIATOR CONTAINER EXISTS FOR meter", meter_id=meter['id'])
                    continue

                mediator_port = mediator_container.labels['listen_port']

                env_vars = {
                    "METER_ID": meter['id'],
                    "MEDIATOR_PORT": mediator_port,
                    "SUPABASE_URL": supabase_url,
                    "SUPABASE_KEY": supabase_key,
                    "FLOWS_ROLE_KEY": flows_role_key,

                }

                container_name = f"{self.job_name.replace('_', '-')}-{meter['ip_address']}"
                command = f"emlite_mediator.jobs.{self.job_name}"

                logger.info('run job',
                            container_name=container_name,
                            meter_id=meter['id'],
                            mediator_port=mediator_port,
                            command=command)

                self.docker_client.containers.run(
                    mediator_image,
                    name=container_name,
                    command=command,
                    environment=env_vars,
                    network_mode="host",
                    detach=True,
                    remove=True,
                )

            time.sleep(30)

        logger.info("finished")

    def _check_environment(self):
        if not mediator_image:
            logger.error("MEDIATOR_IMAGE not set to a docker image.")
            sys.exit(1)

        if not supabase_url or not supabase_key:
            logger.error(
                "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
            sys.exit(2)

        if not flows_role_key:
            logger.error(
                "Environment variable FLOWS_ROLE_KEY not set.")
            sys.exit(3)
