
import time
import datetime
import logging
import os
from supabase import create_client, Client
from kaitaistruct import KaitaiStream, BytesIO

from emlite.api.emlite_api import EmliteAPI
from emlite.messages.emlite_response import EmliteResponse
from ..messages.emlite_object_id_enum import ObjectIdEnum

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
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

        serial = self._read_element_and_deserialise(ObjectIdEnum.serial)
        logger.info("sleep 5 seconds before next request ...")
        time.sleep(5)
        clock_time = self._read_element_and_deserialise(ObjectIdEnum.time)

        logger.info(serial)
        logger.info(clock_time)

    def _read_element_and_deserialise(self, object_id):
        payload_bytes = self.api.read_element(object_id)
        emlite_rsp = EmliteResponse(len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes)))
        emlite_rsp._read()
        data = emlite_rsp.response

        if (object_id == ObjectIdEnum.serial):
            return data.serial.strip()   
        elif (object_id == ObjectIdEnum.time):
            date_obj = datetime.datetime(2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
            return date_obj.isoformat()
        else:
            return payload_bytes

if __name__ == '__main__':
    if not emlite_host or not emlite_port:
        logger.error("Environment variables EMLITE_HOME and EMLITE_PORT not set.")
        exit(1)

    if not supabase_url or not supabase_key:
        logger.error("Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        exit(2)

    syncToDb = SyncToDb()
    syncToDb.sync()