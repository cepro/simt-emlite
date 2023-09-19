from emlite_mediator.util.logging import get_logger

import os

from httpx import ConnectError

from emlite_mediator.jobs.util import check_environment_vars, handle_mediator_unknown_failure, handle_meter_unhealthy_status, handle_supabase_faliure, update_meter_shadows_when_healthy
from emlite_mediator.mediator.client import EmliteMediatorClient, MediatorClientException
from emlite_mediator.util.supabase import supa_client, Client

logger = get_logger(__name__, __file__)

meter_id: str = os.environ.get('METER_ID')

mediator_host: str = os.environ.get('MEDIATOR_HOST') or '0.0.0.0'
mediator_port: str = os.environ.get('MEDIATOR_PORT') or '50051'

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

flows_role_key: str = os.environ.get("FLOWS_ROLE_KEY")

"""
    Fetches the prepay_enabled from the meter and syncs to the shadow table.
"""


class MeterPrepaySyncJob():
    api: EmliteMediatorClient
    supabase: Client

    def __init__(self):
        self.client = EmliteMediatorClient(mediator_host, mediator_port)
        self.supabase = supa_client(supabase_url, supabase_key, flows_role_key)
        global logger
        logger = logger.bind(meter_id=meter_id, mediator_port=mediator_port)

    def sync(self):
        try:
            prepay_enabled = self.client.prepay_enabled()
            logger.info("fetched enabled", prepay_enabled=prepay_enabled)
            prepay_balance = self.client.prepay_balance()
            logger.info("fetched balance", prepay_balance=prepay_balance)
        except MediatorClientException as e:
            handle_meter_unhealthy_status(self.supabase, logger, meter_id, e)
        except Exception as e:
            handle_mediator_unknown_failure(logger, e)

        try:
            #
            # write balance to shadow table
            #
            update_result = update_meter_shadows_when_healthy(
                self.supabase,
                meter_id,
                {
                    "balance": prepay_balance,
                }
            )
            logger.info(
                "updated meter_shadows prepay_balance", update_result=update_result)

            #
            # write enabled flag to registry table only IF it has changed
            #
            meter_registry_record = self.supabase.table('meter_registry').select(
                'prepay_enabled').eq("id", meter_id).execute()
            if (meter_registry_record.data[0]['prepay_enabled'] != prepay_enabled):
                update_result = self.supabase.table('meter_registry').update({
                    "prepay_enabled": prepay_enabled,
                }).eq('id', meter_id).execute()
                logger.info(
                    "updated meter_registry prepay_enabled", update_result=update_result)
            else:
                logger.info("prepay_enabled flag unchanged")

        except ConnectError as e:
            handle_supabase_faliure(logger, e)


if __name__ == '__main__':
    check_environment_vars(logger, supabase_url,
                           supabase_key, flows_role_key, meter_id)

    try:
        job = MeterPrepaySyncJob()
        job.sync()
    except Exception as e:
        logger.error("failure occured syncing prepay info", error=e)
