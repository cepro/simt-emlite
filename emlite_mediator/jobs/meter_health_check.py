import os
import sys

from datetime import datetime
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
        logger.info("checking for %s...", meter_id)

        query_result = None
        try:
            query_result = self.supabase.table('meter_registry').select(
                'serial,hardware').eq("id", meter_id).execute()
        except ConnectError as e:
            handle_supabase_faliure(logger, e)

        if (len(query_result.data) == 0):
            logger.error("no meter_registry record found for this device")
            sys.exit(11)

        reg_rec = query_result.data[0]
        try:
            serial = self._check_serial(
                meter_id, reg_rec['serial'])

            self._check_clock_diff(meter_id)

            registry_hardware = None
            if 'hardware' in reg_rec:
                registry_hardware = reg_rec['hardware']
            self._check_hardware(
                meter_id, registry_hardware, serial)

        except MediatorClientException as e:
            handle_meter_unhealthy_status(self.supabase, logger, meter_id, e)
        except Exception as e:
            handle_mediator_unknown_failure(logger, e)

    """ check the serial matches the one in the registry - if not update the registry """

    def _check_serial(self, id: str, registry_serial: str):
        logger.info("fetch serial ...")
        serial = self.client.serial()

        if (serial == registry_serial):
            logger.info("serial unchanged - no action")
            return serial

        if (registry_serial is None and serial is not None):
            logger.info('add new serial to registry')
        else:
            logger.warning(
                'fetched serial and registry serial [%s] different! '
                'will update the registry with the fetched entry', registry_serial)

        update_result = self.supabase.table('meter_registry').update({
            "serial": serial,
        }).eq('id', id).execute()
        logger.info("update serial result [%s]", update_result)

        return serial

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

        update_result = update_meter_shadows_when_healthy(
            self.supabase,
            id,
            {
                "clock_time_diff_seconds": clock_time_diff_seconds
            }
        )
        logger.info("update_result [%s]", update_result)

    """ check the hardware matches the one in the registry - if not update the registry """

    def _check_hardware(self, id: str, registry_hardware: str, serial: str):
        # if 3 phase meter hardware fetch will fail.
        #
        # currently we have no other way to query the hardware so we check the
        # serial prefix and hardcode the hardware.
        #
        # see also ticket related to this issue on the EMOP downloader:
        #   https://cepro.unfuddle.com/a#/projects/13/tickets/by_number/390
        if serial.startswith('EMP1AX'):
            hardware = 'P1.ax'
        else:
            logger.info("fetch hardware ...")
            hardware = self.client.hardware()

        if (hardware == registry_hardware):
            logger.info("hardware unchanged - no action")
            return

        if (registry_hardware is None and hardware is not None):
            logger.info('add new hardware [%s] to registry', hardware)
        else:
            logger.warning(
                'fetched hardware and registry hardware [%s] different! '
                'will update the registry with the fetched entry', registry_hardware)

        logger.info(
            'skipping db update for now - need to discuss hardware types first')
        # update_result = self.supabase.table('meter_registry').update({
        #     "hardware": hardware,
        # }).eq('id', id).execute()
        # logger.info("update hardware result [%s]", update_result)


if __name__ == '__main__':
    check_environment_vars(logger, supabase_url, supabase_key, meter_id)

    try:
        job = MeterHealthCheckJob()
        job.check_health()
    except Exception as e:
        logger.exception("failure occured checking meter health [%s]", e)
