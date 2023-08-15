import os
import sys

from datetime import datetime
import time
from httpx import ConnectError
from supabase import create_client, Client
from resource import getrusage, RUSAGE_SELF

from emlite_mediator.mediator.client import EmliteMediatorClient
from emlite_mediator.util.logging import get_logger

logger = get_logger(__name__)

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

    def sync(self):
        try:
            csq = self.client.csq()
        except Exception as e:
            logger.error("failure connecting to meter or mediator [%s]", e)
            sys.exit(10)

        try:
            time.sleep(1)
            update_result = self.supabase.table('meter_shadows').update(
                {"csq": csq, "updated_at": datetime.utcnow().isoformat()}).eq('id', meter_id).execute()
        except ConnectError as e:
            logger.error("Supabase connection failure [%s]", e)
            sys.exit(11)

        time.sleep(1)

        print(getrusage(RUSAGE_SELF))

        logger.info("update csq result [%s]", update_result)


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
        job = MeterCsqSyncJob()
        job.sync()
    except Exception as e:
        logger.exception("failure occured syncing csq [%s]", e)
