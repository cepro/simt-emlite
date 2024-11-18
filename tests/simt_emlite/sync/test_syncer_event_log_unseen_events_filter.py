import inspect
import unittest
from typing import List

from emop_frame_protocol.emop_message import EmopMessage

from simt_emlite.sync.syncer_event_log import filter_event_log_for_unseen_events

EventIdType = EmopMessage.EventIdType
EventRec = EmopMessage.EventRec


ONE_DAY_SECONDS = 1440


def add_days(ts: int, days: int) -> int:
    return ts + (days * ONE_DAY_SECONDS)


class TestSyncerEventLogUnseenEventsFilter(unittest.TestCase):
    def test_no_events(self):
        self.assertEqual(
            filter_event_log_for_unseen_events([], None),
            [],
        )

    def test_one_new_event(self):
        time_seconds = 784598400  # 11/11/2024 0:00

        events: List[EventRec] = [
            self._event(time_seconds, EventIdType.daily_log_snapshot, 5),
            self._event(time_seconds, EventIdType.billing_log_snapshot, 3),
            self._event(add_days(time_seconds, 1), EventIdType.daily_log_snapshot, 6),
        ]

        last_seen_event = events[1]

        unseen = filter_event_log_for_unseen_events(events, last_seen_event)
        self.assertEqual(1, len(unseen))
        self.assertEqual(events[2], unseen[0])  # identity same

    def _event(self, ts: int, id: EventIdType, seq: int) -> EventRec:
        event = EventRec()
        event.timestamp = ts
        event.event_id = id
        event.event_seq = seq
        return event
