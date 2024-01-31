import os

from typing import Dict, NamedTuple, Optional
from emlite_mediator.util.logging import get_logger

from abc import ABC, abstractmethod

from httpx import ConnectError
from emlite_mediator.jobs.util import handle_mediator_unknown_failure, handle_meter_unhealthy_status, handle_supabase_faliure, update_meter_shadows_when_healthy
from emlite_mediator.util.supabase import supa_client, Client as SupabaseClient
from emlite_mediator.mediator.client import EmliteMediatorClient, MediatorClientException

logger = get_logger(__name__, __file__)

supabase_url_extra: str = os.environ.get("SUPABASE_URL_EXTRA")
supabase_key_extra: str = os.environ.get("SUPABASE_KEY_EXTRA")
flows_role_key_extra: str = os.environ.get("FLOWS_ROLE_KEY_EXTRA")

sync_extra: bool = all(
    [supabase_url_extra, supabase_key_extra, flows_role_key_extra])


class UpdatesTuple(NamedTuple):
    shadow: Optional[Dict[str, any]]
    registry: Optional[Dict[str, any]]


class SyncerBase(ABC):

    def __init__(
        self,
        supabase: SupabaseClient,
        emlite_client: EmliteMediatorClient,
        meter_id: str
    ):
        self.supabase = supabase
        self.emlite_client = emlite_client
        self.meter_id = meter_id

        self.supabase_extra = None
        if (sync_extra == True):
            self.supabase_extra = supa_client(
                supabase_url_extra, supabase_key_extra, flows_role_key_extra)

        global logger
        logger = logger.bind(meter_id=meter_id, syncer=self.__class__.__name__)

    def sync(self):
        """ Main function invoked to perform the syncing flow.

        First metrics are fetched. see fetch_metrics implementations in each
        syncer subclass.

        Next depending on the data set by the subclasses the meter shadow and
        registry tables are updated
        """
        updates: UpdatesTuple = self.fetch_metrics_with_error_handling()
        if updates == None:
            return

        if updates.shadow:
            self._update_shadow(updates.shadow)

        if updates.registry:
            self._update_registry(updates.registry)

    def fetch_metrics_with_error_handling(self) -> UpdatesTuple:
        try:
            return self.fetch_metrics()
        except MediatorClientException as e:
            handle_meter_unhealthy_status(
                self.supabase, self.supabase_extra, logger, self.meter_id, e)
        except Exception as e:
            handle_mediator_unknown_failure(logger, e)

    @abstractmethod
    def fetch_metrics(self) -> UpdatesTuple:
        pass

    def _update_shadow(self, update_props: Dict[str, any]):
        logger.info("update shadow props", meter_id=self.meter_id,
                    update_props=update_props)
        try:
            update_meter_shadows_when_healthy(
                self.supabase,
                self.meter_id,
                update_props
            )
        except ConnectError as e:
            handle_supabase_faliure(logger, e)

        # sync to extra database and don't terminate if this fails
        try:
            update_meter_shadows_when_healthy(
                self.supabase_extra,
                self.meter_id,
                update_props
            )
        except ConnectError as e:
            logger.error(
                "Supabase connection failure on extra supabase handle, skipping ...", error=e)

    def _update_registry(self, update_props: Dict[str, any]):
        logger.info("update registry props",
                    meter_id=self.meter_id, update_props=update_props)
        try:
            # first fetch existing values and build map of differences
            query_result = self.supabase.table('meter_registry').select(
                ','.join(update_props.keys())).eq("id", self.meter_id).execute()
            current_record = query_result.data[0]

            modified_or_new = {}
            for key in current_record:
                if update_props[key] != current_record[key]:
                    logger.info('value update',
                                key=key, old_value=current_record[key], new_value=update_props[key])
                    modified_or_new[key] = update_props[key]
                else:
                    logger.info('value unchanged, skipping ...',
                                key=key, value=current_record[key])

            # second update the registry with any changes
            if len(modified_or_new.keys()) > 0:
                update_result = self.supabase.table('meter_registry').update(
                    modified_or_new
                ).eq('id', self.meter_id).execute()
                logger.info(
                    "updated meter_registry", update_result=update_result)

        except ConnectError as e:
            handle_supabase_faliure(logger, e)
