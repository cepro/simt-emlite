import inspect
import unittest
from typing import List

from emop_frame_protocol.emop_message import EmopMessage

from simt_emlite.sync.syncer_event_log import filter_event_log_for_unseen_events

EventIdType = EmopMessage.EventIdType
EventRec = EmopMessage.EventRec


ONE_DAY_SECONDS = 1440

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
    event(add_days(START_TIME_SECONDS, 1), EventIdType.daily_log_snapshot, set=4),
    event(add_days(START_TIME_SECONDS, 1), 52, set=0),
    event(add_days(START_TIME_SECONDS, 1), EventIdType.billing_log_snapshot, set=6),
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

    def test_one_new_event(self):
        last_seen_event = EVENTS[8]

        unseen = filter_event_log_for_unseen_events(EVENTS, last_seen_event)
        self.assertEqual(1, len(unseen))
        self.assertEqual(EVENTS[9], unseen[0])  # identity same
