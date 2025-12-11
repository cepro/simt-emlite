import argparse
import os
import sys
import time
import traceback


from tenacity import retry, stop_after_attempt, wait_fixed

from simt_emlite.orchestrate.adapter.container import ContainerState
from simt_emlite.orchestrate.adapter.factory import get_instance
from simt_emlite.orchestrate.adapter.fly_adapter import FLY_STATUS, FlyAdapter
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
flows_role_key: str | None = os.environ.get("FLOWS_ROLE_KEY")
max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS") or 5)
env_code: str | None = os.environ.get("ENV")

"""
    Run simt-emlite job mediators_recover_failed to recreate any failed state
    mediator machines.

    See this Notion task for some background:
    https://www.notion.so/Mediator-fly-machines-in-failed-state-15560033463e808cb863de7178275f2b
"""


class MediatorsRecoverFailedJob:
    def __init__(
        self,
        esco=None,
    ):
        global logger
        self.log = logger.bind(esco=esco)

        self._check_environment()

        # Narrow types after environment check
        assert supabase_url is not None
        assert supabase_key is not None

        self.esco = esco

        self.containers = get_instance(esco=esco, env=env_code)
        self.supabase = supa_client(supabase_url, supabase_key, flows_role_key)

    def run(self):
        self.log.info("starting ...")

        # can probably just use FLY_APP_NAME here:
        app_name = f"mediators-{env_code}-{self.esco}"
        self.log.info(f"app is {app_name}")

        if not isinstance(self.containers, FlyAdapter):
            raise Exception("This job only works with FlyAdapter")

        machines = self.containers.api.list(app=app_name)
        self.log.info(f"machines {machines}")

        machines = list(
            filter(
                lambda m: m["state"] is not None
                and m["state"] == FLY_STATUS[ContainerState.FAILED],
                machines,
            )
        )
        self.log.info(f"failed state machine records [{machines}]")
        self.log.info(f"{len(machines)} machines in failed state")

        if len(machines) == 0:
            sys.exit()

        # TODO: for now just loop instead of parallel
        # - lost logging locally and just go slow until happy the script works well
        for m in machines:
            self.recover_mediator(m)

        # with concurrent.futures.ThreadPoolExecutor(
        #     max_workers=max_parallel_jobs
        # ) as executor:
        #     futures = [
        #         executor.submit(self.recover_mediator, machine) for machine in machines
        #     ]

        # concurrent.futures.wait(futures)

        self.log.info("finished")

    def recover_mediator(self, machine_rec):
        machine_id = machine_rec["id"]
        meter_serial = machine_rec["name"].replace("mediator-", "")
        self.log.info(f"recover_mediator {machine_id} {meter_serial}")

        try:
            self._destroy_failed_mediator(machine_id)

            # wait 20 seconds for fly to clean up the machine
            time.sleep(20)

            self._recreate_failed_mediator(
                meter_serial,
                machine_rec["config"]["metadata"]["emlite_host"],
                machine_rec["config"]["metadata"]["meter_id"],
                # for now reuse the prior port - later after port allocation is fixed just the let the create function allocate it
                machine_rec["config"]["services"][0]["ports"][0]["port"],
            )
        except Exception as e:
            self.log.error(
                "failure occured recovering machine",
                error=e,
                exception=traceback.format_exception(e),
            )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
    def _destroy_failed_mediator(self, machine_id):
        destroy_rsp = self.containers.destroy(id=machine_id, force=True)
        if (
            destroy_rsp is not None
            and "ok" in destroy_rsp
            and destroy_rsp["ok"] is True
        ):
            self.log.info("destroy success", machine_id=machine_id)
        else:
            raise Exception(
                "destroy failed (possibly failed if no response)",
                machine_id,
                self._destroy_failed_mediator.statistics["attempt_number"],  # type: ignore[attr-defined]
            )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
    def _recreate_failed_mediator(self, meter_serial, ip_address, meter_id, port):
        container_id: str = self.containers.create(
            cmd="simt_emlite.mediator.grpc.server",
            serial=meter_serial,
            ip_address=ip_address,
            meter_id=meter_id,
            port=port,
            skip_confirm=True,
        )
        if container_id is not None:
            self.log.info("recreated mediator success", serial=meter_serial)
        else:
            raise Exception(
                "create failed (possibly failed if no response)",
                meter_serial,
                self._recreate_failed_mediator.statistics["attempt_number"],  # type: ignore[attr-defined]
            )

    def _check_environment(self):
        if not supabase_url or not supabase_key:
            self.log.error(
                "Environment variables SUPABASE_URL and SUPABASE_ANON_KEY not set."
            )
            sys.exit(2)

        if not flows_role_key:
            self.log.error("Environment variable FLOWS_ROLE_KEY not set.")
            sys.exit(3)

        if not os.environ.get("FLY_API_TOKEN"):
            self.log.error("Environment variable FLY_API_TOKEN not set.")
            sys.exit(4)

        if not os.environ.get("SIMT_EMLITE_IMAGE"):
            self.log.error("Environment variable SIMT_EMLITE_IMAGE not set.")
            sys.exit(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--esco",
        required=True,
        action="store",
        help="Check meters in this esco only",
    )
    args = parser.parse_args()

    esco = args.esco

    runner = MediatorsRecoverFailedJob(esco=esco)
    runner.run()
