import os
import sys

from datetime import datetime
from httpx import ConnectError
from supabase import create_client, Client

from emlite_mediator.mediator.client import EmliteMediatorClient
from emlite_mediator.util.logging import get_logger

logger = get_logger(__name__)

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
        except Exception as e:
            logger.error("failure connecting to meter or mediator [%s]", e)
            sys.exit(10)

        try:
            #
            # write balance to shadow table
            #
            update_shadow_result = self.supabase.table('meter_shadows').update(
                {"balance": prepay_balance, "updated_at": datetime.utcnow().isoformat()}).eq('id', meter_id).execute()
            logger.info(
                "update prepay_balance result [%s]", update_shadow_result)

            #
            # write enabled flag to registry table only IF it has changed
            #
            meter_registry_record = self.supabase.table('meter_registry').select(
                'prepay_enabled').eq("id", meter_id).execute()
            if (meter_registry_record.data[0]['prepay_enabled'] != prepay_enabled):
                update_registry_result = self.supabase.table('meter_registry').update(
                    {"prepay_enabled": prepay_enabled, "updated_at": datetime.utcnow().isoformat()}).eq('id', meter_id).execute()
                logger.info(
                    "update prepay_enabled result [%s]", update_registry_result)
            else:
                logger.info("prepay_enabled flag unchanged")

        except ConnectError as e:
            logger.error("Supabase connection failure [%s]", e)
            sys.exit(11)


if __name__ == '__main__':
    if not supabase_url or not supabase_key:
        logger.error(
            "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        sys.exit(1)

    if not meter_id:
        logger.error(
            "Environment variable METER_ID not set.")
        sys.exit(2)

    try:
        job = MeterPrepaySyncJob()
        job.sync()
    except Exception as e:
        logger.exception("failure occured syncing prepay_enabled [%s]", e)
