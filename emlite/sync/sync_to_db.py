
import time
import logging
import os

from datetime import datetime
from supabase import create_client, Client
from kaitaistruct import KaitaiStream, BytesIO

from emlite.api.emlite_api import EmliteAPI
from emlite.messages.emlite_response import EmliteResponse
from ..messages.emlite_object_id_enum import ObjectIdEnum

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

emlite_host: str = os.environ.get('EMLITE_HOST')
emlite_port: str = os.environ.get('EMLITE_PORT')

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

class SyncToDb():
    api: EmliteAPI
    supabase: Client

    def __init__(self):
        self.api = EmliteAPI(emlite_host, emlite_port)
        self.supabase = create_client(supabase_url, supabase_key)

    def sync(self):
        logger.info("syncing ...")

        meter_registry_record = self.supabase.table('meter_registry').select('id,serial').eq("ip_address", emlite_host).execute()
        if (len(meter_registry_record.data) == 0):
            logger.error("no meter_registry record found for this device")
            exit()
        
        reg_rec = meter_registry_record.data[0]
        reg_id: str = reg_rec['id']
        
        if (reg_rec['serial'] == None):
            self._sync_serial(reg_id)
        else:
            logger.debug('serial already synced')

        self._sync_clock_diff(reg_id)
            

    """ check if serial is in the registry - if not then fetch and populate it """
    def _sync_serial(self, id: str):
        serial = self._read_element_and_deserialise(ObjectIdEnum.serial)
        
        logger.info("write serial %s to db", serial)
        update_result = self.supabase.table('meter_registry').update({"serial": serial, "updated_at": self._now_ts_str()}).eq('id', id).execute()
        logger.info("update_result %s", update_result)
        self._sleep()   

    """ 
        get the difference between the meter device time and this hosts time in seconds
        (millis are not available from the meter)
    """
    def _sync_clock_diff(self, id: str):
        clock_time: datetime = self._read_element_and_deserialise(ObjectIdEnum.time)
        logger.info("clock_time = %s", clock_time)
        now = datetime.utcnow()
        clock_time_diff_seconds = abs(now - clock_time).seconds
        logger.info("clock_time_diff_seconds = %s", clock_time_diff_seconds)

        update_result = self.supabase.table('meter_shadows').update({"clock_time_diff_seconds": clock_time_diff_seconds, "updated_at": self._now_ts_str()}).eq('id', id).execute()
        logger.info("update_result %s", update_result)
        self._sleep()

    def _read_element_and_deserialise(self, object_id):
        payload_bytes = self.api.read_element(object_id)
        emlite_rsp = EmliteResponse(len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes)))
        emlite_rsp._read()
        data = emlite_rsp.response

        if (object_id == ObjectIdEnum.serial):
            return data.serial.strip()   
        elif (object_id == ObjectIdEnum.time):
            return datetime(2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        else:
            return payload_bytes

    """ The meter can't handle back to back socket close then open's so sleep a bit in between each """
    def _sleep(self):
        sleep_seconds = 4
        logger.info("sleep %s seconds before next request to meter ...", sleep_seconds)
        time.sleep(sleep_seconds)

    def _now_ts_str(self):
        return datetime.utcnow().isoformat()
    
if __name__ == '__main__':
    if not emlite_host or not emlite_port:
        logger.error("Environment variables EMLITE_HOST and EMLITE_PORT not set.")
        exit(1)

    if not supabase_url or not supabase_key:
        logger.error("Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        exit(2)

    syncToDb = SyncToDb()
    syncToDb.sync()