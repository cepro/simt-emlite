
import docker
import logging
import os
import time

from supabase import create_client, Client

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

sync_image: str = os.environ.get("SYNC_IMAGE")
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

filter_connected = lambda meter: meter['ip_address'] is not None

class RunHealthChecks():
    supabase: Client
    docker_client: docker.DockerClient

    def __init__(self):
        self.supabase = create_client(supabase_url, supabase_key)
        self.docker_client = docker.from_env()

    def run(self):
        logger.info("starting ...")

        registry_result = self.supabase.table('meter_registry').select('id,ip_address,serial').execute()
        if (len(registry_result.data) == 0):
            logger.error("no meters record found")
            exit()
        
        meters = list(filter(filter_connected, registry_result.data))
        for meter in meters:
            logger.info(
                "sync meter [serial=%s, ip=%s]",
                    meter['serial'] if 'serial' in meter else 'unknown',
                    meter['ip_address']
            )
            
            env_vars = {
                "EMLITE_HOST": meter['ip_address'],
                "SUPABASE_URL": supabase_url,
                "SUPABASE_KEY": supabase_key
            }

            self.docker_client.containers.run(
                sync_image,
                environment=env_vars,
                network_mode="host",
                detach=True,
                remove=True,
            )

            # Slow down invocation a litte just so we don't fire off all at the same time.
            # Each takes less than 10 seconds to run so this sleep results in 3 or 4 running
            # in parallel at a time. 
            time.sleep(3)

    
if __name__ == '__main__':
    if not sync_image:
        logger.error("SYNC_IMAGE not set to a docker image.")
        exit(1)
    if not supabase_url or not supabase_key:
        logger.error("Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        exit(2)

    syncers = RunHealthChecks()
    syncers.run()