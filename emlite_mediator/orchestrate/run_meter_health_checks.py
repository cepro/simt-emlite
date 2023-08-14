
from typing import List
import docker
import os
import sys
import time

from emlite_mediator.util.logging import get_logger
from emlite_mediator.orchestrate.mediators import Mediators
from supabase import create_client, Client

logger = get_logger(__name__)

mediator_image: str = os.environ.get("MEDIATOR_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")


def filter_connected(meter): return meter['ip_address'] is not None


class RunHealthChecks():
    supabase: Client
    docker_client: docker.DockerClient

    def __init__(self):
        self.supabase = create_client(supabase_url, supabase_key)
        self.docker_client = docker.from_env()
        self.mediators = Mediators()

    def run(self):
        logger.info("%s starting ...", __name__)

        registry_result = self.supabase.table(
            'meter_registry').select('id,ip_address,serial').order(column='serial').execute()
        if (len(registry_result.data) == 0):
            logger.error("no meters record found")
            sys.exit(11)

        meters = list(filter(filter_connected, registry_result.data))

        # process meter health checks in chunks of chunk_size to avoid
        # running out of memory from starting mediators
        chunk_size = 5
        num_chunks = (len(meters) // chunk_size) + 1
        for chunk_idx in list(range(0, num_chunks)):
            range_start = chunk_idx * chunk_size
            range_end = range_start + chunk_size
            chunk_meters = meters[range_start:range_end]

            for meter in chunk_meters:
                logger.info(
                    "meter [serial=%s, ip=%s]",
                    meter['serial'] if 'serial' in meter else 'unknown',
                    meter['ip_address']
                )

                mediator_port = self.mediators.start_one(meter['id'])

                env_vars = {
                    "METER_ID": meter['id'],
                    "MEDIATOR_PORT": mediator_port,
                    "SUPABASE_URL": supabase_url,
                    "SUPABASE_KEY": supabase_key
                }

                logger.info('health_check meter=%s mediator port=%s',
                            meter['id'], mediator_port)

                self.docker_client.containers.run(
                    mediator_image,
                    name=f"meter-health-check-{meter['ip_address']}",
                    command="emlite_mediator.jobs.meter_health_check",
                    environment=env_vars,
                    network_mode="host",
                    detach=True,
                    remove=True,
                )

                # Slow down invocation a litte just so we don't fire off all at the same time.
                # Each takes less than 10 seconds to run so this sleep results in 3 or 4 running
                # in parallel at a time.

                # DISABLED whilst we have chunking in place:
                # time.sleep(3)

            self._stop_mediators(
                list(map(lambda meter: meter['id'], chunk_meters)))

    def _stop_mediators(self, meter_ids: List[str]):
        for meter_id in meter_ids:
            logger.info(
                "stopping mediator for meter [%s]", meter_id)
            self.mediators.stop_one(meter_id)
            time.sleep(1)


if __name__ == '__main__':
    if not mediator_image:
        logger.error("MEDIATOR_IMAGE not set to a docker image.")
        sys.exit(1)

    if not supabase_url or not supabase_key:
        logger.error(
            "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        sys.exit(2)

    checks = RunHealthChecks()
    checks.run()
