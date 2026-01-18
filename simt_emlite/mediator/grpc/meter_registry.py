
import threading
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager

from simt_emlite.emlite.emlite_api import EmliteAPI
from simt_emlite.util.config import load_config
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client, as_list

logger = get_logger(__name__, __file__)

# Constants
MINIMUM_TIME_BETWEEN_REQUESTS_SECONDS = 2
REGISTRY_REFRESH_INTERVAL_SECONDS = 300
LOCK_TIMEOUT_SECONDS = 60.0

@contextmanager
def acquire_timeout(lock, timeout):
    result = lock.acquire(timeout=timeout)
    if not result:
        raise TimeoutError("Could not acquire lock")
    try:
        yield
    finally:
        lock.release()

class MeterContext:
    """
    Holds the state for a specific physical meter.
    """
    def __init__(self, serial: str, host: str, port: int = 8080):
        self.serial = serial
        self.host = host
        self.port = port
        self.api = EmliteAPI(host, port)
        # THE KEY COMPONENT: A lock restricted to this specific meter instance
        self.lock = threading.Lock()
        self.last_request_datetime: Optional[datetime] = None

    def space_out_requests(self) -> None:
        """
        Ensure we don't spam the specific meter faster than allowed.
        Must be called while holding self.lock.
        """
        if self.last_request_datetime is None:
            return

        next_allowed = self.last_request_datetime + timedelta(
            seconds=MINIMUM_TIME_BETWEEN_REQUESTS_SECONDS
        )
        if datetime.now() < next_allowed:
            wait_time = (next_allowed - datetime.now()).total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)

    def mark_used(self) -> None:
        self.last_request_datetime = datetime.now()

class MeterRegistry:
    """
    Thread-safe registry of known meters.
    Backed by database.
    """
    def __init__(self, esco_code: Optional[str] = None):
        self._meters: Dict[str, MeterContext] = {}
        self._lock = threading.RLock()
        self._last_refresh_time: float = 0.0
        self.esco_code = esco_code

        # Setup DB client
        self.config = load_config()
        self.supabase_url = self.config["supabase_url"]
        self.supabase_anon_key = self.config["supabase_anon_key"]
        self.supabase_access_token = self.config["supabase_access_token"]
        self.supabase = None
        if self.supabase_url and self.supabase_anon_key and self.supabase_access_token:
            self.supabase = supa_client(
                str(self.supabase_url),
                str(self.supabase_anon_key),
                str(self.supabase_access_token)
            )

    def get_meter(self, serial: str) -> Optional[MeterContext]:
        """
        Get a meter context, refreshing from DB if necessary/scheduled.
        """
        # Lazy refresh
        if time.time() - self._last_refresh_time > REGISTRY_REFRESH_INTERVAL_SECONDS:
            self.refresh_from_db()

        with self._lock:
            return self._meters.get(serial)

    def refresh_from_db(self):
        """
        Reload/Sync meter definitions from the database.
        """
        if not self.supabase:
            logger.warning("No database connection for registry refresh")
            return

        logger.info("Refreshing meter registry from database...")
        try:
            esco_id = None

            # If esco_code filter is specified, look up the esco_id
            if self.esco_code:
                escos = (
                    self.supabase.table("escos").select("id").ilike("code", self.esco_code).execute()
                )
                escos_data = as_list(escos)
                if len(escos_data) == 0:
                    logger.error(f"no esco found for {self.esco_code}")
                    return
                esco_id = escos_data[0]["id"]

            # Fetch meters with IP addresses
            query = (
                self.supabase.table("meter_registry")
                .select("serial, ip_address")
            )

            if esco_id is not None:
                query = query.eq("esco", esco_id)

            result = query.execute()

            rows = as_list(result)
            added_count = 0
            updated_count = 0
            with self._lock:
                for row in rows:
                    serial = row.get("serial")
                    ip = row.get("ip_address")
                    # Only register if we have a serial and an IP
                    if serial and ip:
                         if serial not in self._meters:
                             logger.info(f"Adding meter {serial} at {ip}")
                             self._meters[serial] = MeterContext(serial, ip)
                             added_count += 1
                         else:
                             # Update IP if changed
                             if self._meters[serial].host != ip:
                                 logger.info(f"Updating meter {serial} IP to {ip}")
                                 self._meters[serial].host = ip
                                 self._meters[serial].api = EmliteAPI(ip, self._meters[serial].port)
                                 updated_count += 1

                if added_count > 0 or updated_count > 0:
                    logger.info(f"Registry refreshed: {added_count} added, {updated_count} updated. Total meters: {len(self._meters)}")

            self._last_refresh_time = time.time()

        except Exception as e:
            logger.error(f"Failed to refresh registry: {e}")
