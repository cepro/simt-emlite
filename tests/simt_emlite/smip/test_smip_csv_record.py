import unittest
from datetime import datetime, timezone
from simt_emlite.smip.smip_csv_record import SMIPCSVRecord

test_timestamp = datetime(2023, 12, 10, 14, 30, 0, tzinfo=timezone.utc)

class TestSMIPCSVRecord(unittest.TestCase):

    def test_to_csv_line_none_to_na_export(self):
        rec = SMIPCSVRecord(test_timestamp, 12345.0, None)
        csv_line = rec.to_csv_line()
        self.assertTrue(csv_line.endswith(",12345,NA"))

    def test_to_csv_line_none_to_na_import(self):
        rec = SMIPCSVRecord(test_timestamp, None, 56789.0)
        csv_line = rec.to_csv_line()
        self.assertTrue(csv_line.endswith(",NA,56789"))

    def test_to_csv_line_both_values(self):
        rec = SMIPCSVRecord(test_timestamp, 12345.0, 56789.0)
        csv_line = rec.to_csv_line()
        self.assertTrue(csv_line.endswith(",12345,56789"))

if __name__ == '__main__':
    unittest.main()