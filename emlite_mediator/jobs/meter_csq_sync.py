from emlite_mediator.util.logging import get_logger

import os

from httpx import ConnectError
from supabase import create_client, Client

from emlite_mediator.jobs.util import check_environment_vars, handle_mediator_unknown_failure, handle_supabase_faliure, handle_meter_unhealthy_status, update_meter_shadows_when_healthy
from emlite_mediator.mediator.client import EmliteMediatorClient, MediatorClientException

logger = get_logger(__name__, __file__)

meter_id: str = os.environ.get('METER_ID')

mediator_host: str = os.environ.get('MEDIATOR_HOST') or '0.0.0.0'
mediator_port: str = os.environ.get('MEDIATOR_PORT') or '50051'

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

"""
    Fetches the csq from the meter and syncs to the shadow table.
"""


class MeterCsqSyncJob():
    api: EmliteMediatorClient
    supabase: Client

    def __init__(self):
        self.client = EmliteMediatorClient(mediator_host, mediator_port)
        self.supabase = create_client(supabase_url, supabase_key)
        global logger
        logger = logger.bind(meter_id=meter_id, mediator_port=mediator_port)

    def sync(self):
        try:
            csq = self.client.csq()
        except MediatorClientException as e:
            handle_meter_unhealthy_status(self.supabase, logger, meter_id, e)
        except Exception as e:
            handle_mediator_unknown_failure(logger, e)

        try:
            update_result = update_meter_shadows_when_healthy(
                self.supabase,
                meter_id,
                {
                    "csq": csq
                }
            )
        except ConnectError as e:
            handle_supabase_faliure(logger, e)

        logger.info("updated meter_shadows.csq", update_result=update_result)


if __name__ == '__main__':
    check_environment_vars(logger, supabase_url, supabase_key, meter_id)

    try:
        job = MeterCsqSyncJob()
        job.sync()
    except Exception as e:
        logger.exception("failure occured syncing csq")
