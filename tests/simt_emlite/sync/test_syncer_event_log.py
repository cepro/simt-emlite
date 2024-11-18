import unittest
from typing import List

from emop_frame_protocol.emop_message import EmopMessage

from simt_emlite.sync.syncer_event_log import event_rec_to_table_row

EventIdType = EmopMessage.EventIdType
EventRec = EmopMessage.EventRec


START_TIME_SECONDS = 784598400  # 11/11/2024 0:00 in seconds since 01/01/2000
METER_ID = "abd811ea-67ba-468a-a3d0-4cded9439055"


def event(ts: int, id: EventIdType, set: int) -> EventRec:
    event = EventRec()
    event.timestamp = ts
    event.event_id = id
    event.event_set = set
    return event


EVENTS: List[EventRec] = [
    event(START_TIME_SECONDS, EventIdType.daily_log_snapshot, set=4),
    event(START_TIME_SECONDS, 52, set=0),
]


class TestSyncerEventLog(unittest.TestCase):
    def test_event_rec_to_table_row(self):
        event = EVENTS[0]
        self.assertEqual(
            {
                "event_set": event.event_set,
                "event_type": event.event_id.value,
                "meter_id": METER_ID,
                "timestamp": event.timestamp,
            },
            event_rec_to_table_row(METER_ID, EVENTS[0]),
        )
