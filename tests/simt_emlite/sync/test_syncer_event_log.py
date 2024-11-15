import unittest

from simt_emlite.sync.syncer_event_log import filter_event_log_for_unseen_events


class TestSyncerEventLog(unittest.TestCase):
    def test_filter_event_log_for_unseen_events(self):
        self.assertEqual(
            filter_event_log_for_unseen_events([], []),
            [],
        )
