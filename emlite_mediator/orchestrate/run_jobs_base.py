from emlite_mediator.util.logging import get_logger

import concurrent.futures
import docker
import os
import sys
import traceback

from typing import Any, Callable

from emlite_mediator.orchestrate.mediators import Mediators
from emlite_mediator.jobs.meter_sync import MeterSyncJob
from emlite_mediator.util.supabase import supa_client


logger = get_logger(__name__, __file__)

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")
site_code: str = os.environ.get("SITE")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 15)


def filter_connected(meter): return meter['ip_address'] is not None

"""
    This script is a base class for scripts that run a job for all meters.
"""


class RunJobForAllMeters():
    def __init__(self, job_name: str, filter_fn: Callable[[Any], bool] = None, run_frequency=None):
        self._check_environment()
        self.job_name = job_name
        self.filter_fn = filter_fn
        self.supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        self.docker_client = docker.from_env()
        self.mediators = Mediators()
        self.run_frequency = run_frequency

        global logger
        self.log = logger.bind(job_name=job_name)

    def get_mediator_port(self, meter_id):
        mediator_container = self.mediators.container_by_meter_id(meter_id)
        if (mediator_container == None):
            self.log.error(
                "NO MEDIATOR CONTAINER EXISTS FOR meter", meter_id=meter_id)
            return

        return mediator_container.labels['listen_port']

    def run_job(self, meter_id):
        mediator_port = self.get_mediator_port(meter_id)
        if mediator_port == None:
            return

        try:
            self.log.info('run_job', meter_id=meter_id,
                          mediator_port=mediator_port)
            job = MeterSyncJob(
                meter_id=meter_id,
                mediator_port=mediator_port,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                flows_role_key=flows_role_key,
                run_frequency=self.run_frequency
            )
            job.sync()
        except Exception as e:
            self.log.error("failure occured syncing", error=e)
            traceback.print_exc()

    def run(self):
        self.log.info("starting ...")

        sites = self.supabase.table('sites').select(
            'id').ilike('code', site_code).execute()
        if (len(sites.data) == 0):
            self.log.error("no site found for " + site_code)
            sys.exit(10)

        site_id = list(sites.data)[0]['id']

        registry_result = (self.supabase.table('meter_registry')
                           .select('id,ip_address,serial,hardware')

                           # only process meters at the given site
                           .eq('site', site_id)

                           # only sync active / real hardware meters
                           # passive meters are synced from active meters in
                           #   some other database and environment
                           .eq('mode', 'active')

                           .order(column='serial')
                           .execute())
        if (len(registry_result.data) == 0):
            self.log.error("no meters record found")
            sys.exit(11)

        meters = list(filter(filter_connected, registry_result.data))
        if (self.filter_fn):
            meters = list(filter(self.filter_fn, meters))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_jobs) as executor:
            futures = [executor.submit(self.run_job, meter['id'])
                       for meter in meters]

        concurrent.futures.wait(futures)

        self.log.info("finished")

    def _check_environment(self):
        if not supabase_url or not supabase_key:
            self.log.error(
                "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
            sys.exit(2)

        if not flows_role_key:
            self.log.error(
                "Environment variable FLOWS_ROLE_KEY not set.")
            sys.exit(3)
