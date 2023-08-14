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
    Checks meter health by querying some data points and syncing these to the
    meter_registry and meter_shadows tables
"""


class MeterHealthCheckJob():
    api: EmliteMediatorClient
    supabase: Client

    def __init__(self):
        self.client = EmliteMediatorClient(mediator_host, mediator_port)
        self.supabase = create_client(supabase_url, supabase_key)

    def check_health(self):
        logger.info("checking ...")

        meter_registry_record = None
        try:
            meter_registry_record = self.supabase.table('meter_registry').select(
                'serial').eq("id", meter_id).execute()
        except ConnectError as e:
            logger.error("Supabase connection failure [%s]", e)
            sys.exit(10)

        if (len(meter_registry_record.data) == 0):
            logger.error("no meter_registry record found for this device")
            sys.exit(11)

        try:
            self._check_serial(
                meter_id, meter_registry_record.data[0]['serial'])
            self._check_clock_diff(meter_id)
        except Exception as e:
            logger.error("failure connecting to meter or mediator [%s]", e)
            sys.exit(12)

    """ check the serial matches the one in the registry - if not update the registry """

    def _check_serial(self, id: str, registry_serial: str):
        logger.info("fetch serial ...")
        serial = self.client.serial()

        if (serial == registry_serial):
            logger.info("serial unchanged - no action")
            return

        if (registry_serial is None and serial is not None):
            logger.info('add new serial to registry')
        else:
            logger.warning(
                'fetched serial and registry serial [%s] different! '
                'will update the registry with the fetched entry', registry_serial)

        update_result = self.supabase.table('meter_registry').update(
            {"serial": serial, "updated_at": self._now_ts_str()}).eq('id', id).execute()
        logger.info("update serial result [%s]", update_result)

    """ 
        get the clock time and check the difference between the meter device 
        time and this hosts time in seconds (millis are not available from the
        meter)
    """

    def _check_clock_diff(self, id: str):
        logger.info("fetch clock time ...")
        clock_time: datetime = self.client.clock_time()

        now = datetime.utcnow()
        clock_time_diff_seconds = abs(now - clock_time).seconds
        logger.info("clock_time_diff_seconds [%s]", clock_time_diff_seconds)

        update_result = self.supabase.table('meter_shadows').update(
            {"clock_time_diff_seconds": clock_time_diff_seconds, "updated_at": self._now_ts_str()}).eq('id', id).execute()
        logger.info("update_result [%s]", update_result)

    def _now_ts_str(self):
        return datetime.utcnow().isoformat()


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
        job = MeterHealthCheckJob()
        job.check_health()
    except Exception as e:
        logger.exception("failure occured checking meter health [%s]", e)
