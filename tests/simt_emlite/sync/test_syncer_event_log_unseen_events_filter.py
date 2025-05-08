import unittest
from typing import List

from emop_frame_protocol.generated.emop_event_log_response import EmopEventLogResponse

from simt_emlite.sync.syncer_event_log import filter_event_log_for_unseen_events

EventIdType = EmopEventLogResponse.EventIdType
EventRec = EmopEventLogResponse.EventRec


ONE_DAY_SECONDS = 24 * 60 * 60

START_TIME_SECONDS = 784598400  # 11/11/2024 0:00 in seconds since 01/01/2000


def add_days(ts: int, days: int) -> int:
    return ts + (days * ONE_DAY_SECONDS)


def event(ts: int, id: EventIdType, set: int) -> EventRec:
    event = EventRec()
    event.timestamp = ts
    event.event_id = id
    event.event_set = set
    return event


EVENTS: List[EventRec] = [
    event(START_TIME_SECONDS, EventIdType.daily_log_snapshot, set=4),
    event(START_TIME_SECONDS, 52, set=0),
    event(START_TIME_SECONDS, EventIdType.billing_log_snapshot, set=6),
    event(
        # 20:00 on the 11/11/2024
        START_TIME_SECONDS + 20 * 60 * 60,
        EventIdType.listening_socket_aborted,
        set=0,
    ),
    event(add_days(START_TIME_SECONDS, 1), EventIdType.daily_log_snapshot, set=5),
    event(add_days(START_TIME_SECONDS, 1), 52, set=0),
    event(add_days(START_TIME_SECONDS, 1), EventIdType.billing_log_snapshot, set=7),
    event(add_days(START_TIME_SECONDS, 2), EventIdType.daily_log_snapshot, set=6),
    event(add_days(START_TIME_SECONDS, 2), 52, set=0),
    event(add_days(START_TIME_SECONDS, 2), EventIdType.billing_log_snapshot, set=8),
]


class TestSyncerEventLogUnseenEventsFilter(unittest.TestCase):
    def test_no_events(self):
        self.assertEqual(
            filter_event_log_for_unseen_events([], None),
            [],
        )

    def test_first_sync_returns_all(self):
        self.assertEqual(
            filter_event_log_for_unseen_events(EVENTS, None),
            EVENTS,
        )

    def test_next_days_events(self):
        last_seen_event = EVENTS[6]  # last record on 12/11/2024

        unseen = filter_event_log_for_unseen_events(EVENTS, last_seen_event)

        # 3 events on 13/11/2024
        self.assertEqual(3, len(unseen))

        self.assertEqual(EVENTS[7], unseen[0])
        self.assertEqual(EVENTS[8], unseen[1])
        self.assertEqual(EVENTS[9], unseen[2])
