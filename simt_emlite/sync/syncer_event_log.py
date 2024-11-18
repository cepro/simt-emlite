from typing import List

from emop_frame_protocol.emop_message import EmopMessage
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


def filter_event_log_for_unseen_events(
    # events must be in timestamp descending order
    events: List[EmopMessage.EventRec],
    latest_event_in_db,
) -> List[EmopMessage.EventRec]:
    if latest_event_in_db is None:
        return events
    return list(filter(lambda e: e.timestamp > latest_event_in_db.timestamp, events))


def event_rec_to_table_row(
    meter_id: str,
    event: EmopMessage.EventRec,
):
    return {
        "meter_id": meter_id,
        "timestamp": event.timestamp,
        "event_type": event.event_id.value,
        "event_set": event.event_set,
    }


class SyncerEventLog(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        # TODO: most likely we need the following but lets try against 3p meters first:

        # is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        # if is_3p:
        #     return

        result = (
            self.supabase.table("meter_event_log")
            .select("timestamp,event_type,event_set")
            .eq("meter_id", self.meter_id)
            .order(column="timestamp", desc=True)
            .limit(10)
            .execute()
        )
        last_seen_event: EmopMessage.EventLogRec = (
            result.data[0] if len(result.data) > 0 else None
        )
        logger.info("last seen event", last_seen_event=last_seen_event)

        unseen_events: List[EmopMessage.EventLogRec] = self._fetch_unseen(
            last_seen_event=last_seen_event
        )
        logger.info("unseen events", unseen_events=unseen_events)

        insert_recs = list(
            map(
                lambda e: event_rec_to_table_row(meter_id=self.meter_id, event=e),
                unseen_events,
            )
        )
        response = self.supabase.table("meter_event_log").insert(insert_recs).execute()
        print(response)

        return UpdatesTuple(None, None)

    def _fetch_unseen(
        self, last_seen_event: EmopMessage.EventLogRec
    ) -> List[EmopMessage.EventRec]:
        unseen_events_all = []

        sync_more = True
        log_idx = 0
        while sync_more:
            log = self.emlite_client.event_log(log_idx)
            unseen_events = filter_event_log_for_unseen_events(
                log.events, last_seen_event
            )
            logger.info(
                "unseen in current fetched logs", unseen_in_fetched=unseen_events
            )
            unseen_events_all.extend(unseen_events)

            # if all 10 fetched events were new events then we need to look back further
            # TODO: change log_idx restriction to 10 (one above the the maximum)
            #   using 3 for now just to limit how far we go back in this test phase
            log_idx += 1
            sync_more = len(unseen_events) == 10 and log_idx < 3

        return unseen_events_all
