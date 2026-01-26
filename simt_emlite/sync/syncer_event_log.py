# mypy: disable-error-code="import-untyped"
from datetime import datetime
from typing import List

from emop_frame_protocol.generated.emop_event_log_response import EmopEventLogResponse
from emop_frame_protocol.util import (
    emop_datetime_to_epoch_seconds,
    emop_epoch_seconds_to_datetime,
)
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import is_three_phase_lookup

logger = get_logger(__name__, __file__)


def filter_event_log_for_unseen_events(
    # events must be in timestamp descending order
    events: List[EmopEventLogResponse.EventRec],
    latest_event_in_db,
) -> List[EmopEventLogResponse.EventRec]:
    if latest_event_in_db is None:
        return events
    return list(filter(lambda e: e.timestamp > latest_event_in_db.timestamp, events))


def event_rec_to_table_row(
    meter_id: str,
    event: EmopEventLogResponse.EventRec,
):
    return {
        "meter_id": meter_id,
        "timestamp": emop_epoch_seconds_to_datetime(event.timestamp).isoformat(),
        "event_type": event.event_id
        if isinstance(event.event_id, int)
        else event.event_id.value,
        "event_set": event.event_set,
    }


def event_table_row_to_rec(
    row,
) -> EmopEventLogResponse.EventRec:
    event = EmopEventLogResponse.EventRec()
    event.timestamp = emop_datetime_to_epoch_seconds(
        datetime.fromisoformat(row["timestamp"])
    )
    event.event_id = row["event_type"]
    event.event_set = row["event_set"]
    return event


class SyncerEventLog(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        if is_3p:
            return UpdatesTuple(None, None)

        result = (
            self.supabase.table("meter_event_log")
            .select("timestamp,event_type,event_set")
            .eq("meter_id", self.meter_id)
            .order(column="timestamp", desc=True)
            .limit(1)
            .execute()
        )

        last_seen_event_rec = None
        if len(result.data) > 0:
            last_seen_event_row = result.data[0]
            logger.info("last seen event row", last_seen_event=last_seen_event_row)
            last_seen_event_rec = event_table_row_to_rec(last_seen_event_row)

        unseen_events: List[EmopEventLogResponse.EventRec] = self._fetch_unseen(
            last_seen_event=last_seen_event_rec
        )
        logger.info("unseen events count", unseen_event_count=len(unseen_events))

        if len(unseen_events) > 0:
            # Event id 0 is not valid but these were seen in a meter - filter out and warn of these
            unseen_events_filtered = list(
                filter(lambda e: e.event_id != 0, unseen_events)
            )
            if len(unseen_events_filtered) != len(unseen_events):
                logger.warn("ignoring events with event_id 0")

            insert_recs = list(
                map(
                    lambda e: event_rec_to_table_row(meter_id=self.meter_id, event=e),
                    unseen_events_filtered,
                )
            )
            logger.info(
                f"{len(insert_recs)} records to insert", insert_recs=insert_recs
            )

            response = (
                self.supabase.table("meter_event_log")
                .upsert(
                    insert_recs,
                    on_conflict="meter_id,timestamp,event_type",
                    ignore_duplicates=True,
                )
                .execute()
            )
            logger.info("supabase insert response", response=response)

        return UpdatesTuple(None, None)

    def _fetch_unseen(
        self, last_seen_event: EmopEventLogResponse.EventRec
    ) -> List[EmopEventLogResponse.EventRec]:
        unseen_events_all = []

        sync_more = True
        log_idx = 0
        while sync_more:
            log = self.emlite_client.event_log(self.serial, log_idx)
            unseen_events = filter_event_log_for_unseen_events(
                log.events, last_seen_event
            )
            logger.info(
                "unseen in current fetched logs", unseen_in_fetched=unseen_events
            )
            unseen_events_all.extend(unseen_events)

            # if all 10 fetched events were new events then we need to look back further
            log_idx += 1
            sync_more = len(unseen_events) == 10 and log_idx < 10

        return unseen_events_all
