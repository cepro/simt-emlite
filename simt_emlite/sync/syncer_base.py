import os
from abc import ABC, abstractmethod
from typing import Any, Dict, NamedTuple, Optional, cast

from httpx import ConnectError

from simt_emlite.jobs.util import (
    handle_mediator_unknown_failure,
    handle_meter_unhealthy_status,
    handle_supabase_faliure,
    update_meter_shadows_when_healthy,
)
from simt_emlite.mediator.client import EmliteMediatorClient
from simt_emlite.mediator.mediator_client_exception import (
    MediatorClientException,
)
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import Client as SupabaseClient
from simt_emlite.util.supabase import as_first_item, supa_client

logger = get_logger(__name__, __file__)

supabase_url_extra: str | None = os.environ.get("SUPABASE_URL_EXTRA")
supabase_key_extra: str | None = os.environ.get("SUPABASE_ANON_KEY_EXTRA")
flows_role_key_extra: str | None = os.environ.get("FLOWS_ROLE_KEY_EXTRA")

sync_extra: bool = all([supabase_url_extra, supabase_key_extra, flows_role_key_extra])


class UpdatesTuple(NamedTuple):
    shadow: Optional[Dict[str, Any]]
    registry: Optional[Dict[str, Any]]


class SyncerBase(ABC):
    def __init__(
        self,
        supabase: SupabaseClient,
        emlite_client: EmliteMediatorClient,
        meter_id: str,
    ):
        self.supabase = supabase
        self.emlite_client = emlite_client
        self.meter_id = meter_id

        self.supabase_extra: SupabaseClient | None = None
        if sync_extra is True:
            if not supabase_url_extra or not supabase_key_extra:
                raise Exception(
                    "SUPABASE_URL_EXTRA and SUPABASE_ANON_KEY_EXTRA not set"
                )
            self.supabase_extra = supa_client(
                supabase_url_extra, supabase_key_extra, flows_role_key_extra
            )

        global logger
        self.log = logger.bind(meter_id=meter_id, syncer=self.__class__.__name__)

    def sync(self) -> None:
        """Main function invoked to perform the syncing flow.

        First metrics are fetched. see fetch_metrics implementations in each
        syncer subclass.

        Next depending on the data set by the subclasses the meter shadow and
        registry tables are updated
        """
        updates: UpdatesTuple | None = self.fetch_metrics_with_error_handling()
        if updates is None:
            return

        if updates.shadow:
            self._update_shadow(updates.shadow)

        if updates.registry:
            self._update_registry(updates.registry)

    def fetch_metrics_with_error_handling(self) -> UpdatesTuple | None:
        try:
            return self.fetch_metrics()
        except MediatorClientException as e:
            handle_meter_unhealthy_status(
                self.supabase, self.supabase_extra, self.log, self.meter_id, e
            )
        except Exception as e:
            handle_mediator_unknown_failure(self.log, e)
        return None

    @abstractmethod
    def fetch_metrics(self) -> UpdatesTuple:
        pass

    def _update_shadow(self, update_props: Dict[str, Any]):
        self.log.info(
            "update shadow props", meter_id=self.meter_id, update_props=update_props
        )
        try:
            update_meter_shadows_when_healthy(
                self.supabase, self.meter_id, update_props
            )
        except ConnectError as e:
            handle_supabase_faliure(self.log, e)
            return

        if sync_extra is True and self.supabase_extra:
            # sync to extra database and don't terminate if this fails
            try:
                update_meter_shadows_when_healthy(
                    cast(SupabaseClient, self.supabase_extra),
                    self.meter_id,
                    update_props,
                )
            except ConnectError as e:
                self.log.error(
                    "Supabase connection failure on extra supabase handle, skipping ...",
                    error=e,
                )

    def _update_registry(self, update_props: Dict[str, Any]):
        self.log.info(
            "update registry props", meter_id=self.meter_id, update_props=update_props
        )
        try:
            # first fetch existing values and build map of differences
            query_result = (
                self.supabase.table("meter_registry")
                .select(",".join(update_props.keys()))
                .eq("id", self.meter_id)
                .execute()
            )
            current_record = as_first_item(query_result)

            modified_or_new = {}
            for key in current_record:
                if update_props[key] != current_record[key]:
                    self.log.info(
                        "value update",
                        key=key,
                        old_value=current_record[key],
                        new_value=update_props[key],
                    )
                    modified_or_new[key] = update_props[key]
                else:
                    self.log.info(
                        "value unchanged, skipping ...",
                        key=key,
                        value=current_record[key],
                    )

            # second update the registry with any changes
            if len(modified_or_new.keys()) > 0:
                update_result = (
                    self.supabase.table("meter_registry")
                    .update(modified_or_new)
                    .eq("id", self.meter_id)
                    .execute()
                )
                self.log.info("updated meter_registry", update_result=update_result)

        except ConnectError as e:
            handle_supabase_faliure(self.log, e)
