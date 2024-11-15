from typing import List

from emop_frame_protocol.emop_message import EmopMessage
from typing_extensions import override

from simt_emlite.sync.syncer_base import SyncerBase, UpdatesTuple
from simt_emlite.util.meters import is_three_phase_lookup


def filter_event_log_for_unseen_events(
    # events must be in timestamp descending order
    events: List[EmopMessage.EventRec],
    latest_event_in_db,
) -> List[EmopMessage.EventRec]:
    return list(filter(lambda e: e.timestamp > latest_event_in_db.timestamp, events))


class SyncerEventLog(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        # TODO: most likely we need the following but lets try against 3p meters first:

        # is_3p = is_three_phase_lookup(self.supabase, self.meter_id)
        # if is_3p:
        #     return

        result = (
            self.supabase.table("meter_event_log")
            .select("timestamp,event_type,event_seq")
            .eq("id", self.meter_id)
            .order(desc=True)
            .limit(10)
            .execute()
        )
        most_recent_entry = result.data[0]

        print(f"most_recent_entry = {most_recent_entry}")

        sync_more = True
        while sync_more:
            log = self.emlite_client.event_log()

            unseen_events = []

            print(f"new_events = [{unseen_events}]")

            # sync more if all 10 fetched events were new events
            sync_more = len(unseen_events) == 10

        return UpdatesTuple(None, None)
