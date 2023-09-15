import os

from httpx import ConnectError
from supabase import create_client, Client
from emlite_mediator.jobs.util import check_environment_vars, handle_mediator_unknown_failure, handle_meter_unhealthy_status, handle_supabase_faliure, now_iso_str, update_meter_shadows_when_healthy

from emlite_mediator.mediator.client import EmliteMediatorClient, MediatorClientException
from emlite_mediator.util.logging import get_logger

logger = get_logger(__name__, __file__)

meter_id: str = os.environ.get('METER_ID')

mediator_host: str = os.environ.get('MEDIATOR_HOST') or '0.0.0.0'
mediator_port: str = os.environ.get('MEDIATOR_PORT') or '50051'

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

"""
    Fetches the prepay_enabled from the meter and syncs to the shadow table.
"""


class MeterPrepaySyncJob():
    api: EmliteMediatorClient
    supabase: Client

    def __init__(self):
        self.client = EmliteMediatorClient(mediator_host, mediator_port)
        self.supabase = create_client(supabase_url, supabase_key)

    def sync(self):
        try:
            prepay_enabled = self.client.prepay_enabled()
            logger.info("enabled [%s]", prepay_enabled)
            prepay_balance = self.client.prepay_balance()
            logger.info("balance [%s]", prepay_balance)
        except MediatorClientException as e:
            handle_meter_unhealthy_status(self.supabase, logger, meter_id, e)
        except Exception as e:
            handle_mediator_unknown_failure(logger, e)

        try:
            #
            # write balance to shadow table
            #
            update_shadow_result = update_meter_shadows_when_healthy(
                self.supabase,
                meter_id,
                {
                    "balance": prepay_balance,
                }
            )
            logger.info(
                "update prepay_balance result [%s]", update_shadow_result)

            #
            # write enabled flag to registry table only IF it has changed
            #
            meter_registry_record = self.supabase.table('meter_registry').select(
                'prepay_enabled').eq("id", meter_id).execute()
            if (meter_registry_record.data[0]['prepay_enabled'] != prepay_enabled):
                update_registry_result = self.supabase.table('meter_registry').update({
                    "prepay_enabled": prepay_enabled,
                }).eq('id', meter_id).execute()
                logger.info(
                    "update prepay_enabled result [%s]", update_registry_result)
            else:
                logger.info("prepay_enabled flag unchanged")

        except ConnectError as e:
            handle_supabase_faliure(logger, e)


if __name__ == '__main__':
    check_environment_vars(logger, supabase_url, supabase_key, meter_id)

    try:
        job = MeterPrepaySyncJob()
        job.sync()
    except Exception as e:
        logger.exception("failure occured syncing prepay_enabled [%s]", e)
