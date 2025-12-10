import unittest
import os
from simt_emlite.smip.smip_csv import SMIPCSV
from simt_emlite.smip.smip_csv_record import SMIPCSVRecord

class TestSMIPCSV(unittest.TestCase):

    def test_read_smip_file_with_nas(self):
        """Test reading SMIP file with NA values (should be skipped)"""
        # A number of records with NA values skipped (see unfuddle #410)
        test_file = os.path.join(os.path.dirname(__file__), 'test_data', 'EML2207642296-20221013.csv')

        records = SMIPCSV.read_from_file(test_file)

        # Expected: 13 records (after skipping NA values)
        self.assertEqual(13, len(records))

        # Check the first record was read correctly
        rec1 = records[0]
        self.assertAlmostEqual(501.331, rec1.import_value, places=3)
        self.assertAlmostEqual(2.212, rec1.export_value, places=3)

        # Check the last record was read correctly
        recN = records[-1]
        self.assertAlmostEqual(501.331, recN.import_value, places=3)
        self.assertAlmostEqual(2.245, recN.export_value, places=3)

    def test_read_smip_file_all_nas(self):
        """Test reading SMIP file with all NA values (should return empty list)"""
        test_file = os.path.join(os.path.dirname(__file__), 'test_data', 'EML2137580799-A-20211210.csv')

        records = SMIPCSV.read_from_file(test_file)

        # Expected: 0 records (all values are NA)
        self.assertEqual(0, len(records))

    def test_read_smip_file_with_neg1s(self):
        """Test reading SMIP file with -1 values (should be skipped)"""
        test_file = os.path.join(os.path.dirname(__file__), 'test_data', 'EML2137580799-A-20211203.csv')

        records = SMIPCSV.read_from_file(test_file)

        # Expected: 40 records (after skipping -1 values)
        self.assertEqual(40, len(records))

        # Check the first record was read correctly
        rec1 = records[0]
        self.assertAlmostEqual(26.559, rec1.import_value, places=3)
        self.assertAlmostEqual(0.0, rec1.export_value, places=3)

        # Check the last record was read correctly
        recN = records[-1]
        self.assertAlmostEqual(30.818, recN.import_value, places=3)
        self.assertAlmostEqual(0.0, recN.export_value, places=3)

    def test_read_smip_string(self):
        """Test reading SMIP data from a string"""
        csv_data = """\"created_at\",\"EML123456789\",\"EML123456789_rev\"
2023-12-10 14:30:00+0000,123450,567890
2023-12-10 15:00:00+0000,123500,567900
2023-12-10 15:30:00+0000,NA,567910
2023-12-10 16:00:00+0000,123550,-1"""

        records = SMIPCSV.read(csv_data)

        # Expected: 2 records (skipping NA and -1 values)
        self.assertEqual(2, len(records))

        # Check first record
        rec1 = records[0]
        self.assertAlmostEqual(123.450, rec1.import_value, places=3)
        self.assertAlmostEqual(567.890, rec1.export_value, places=3)

        # Check second record
        rec2 = records[1]
        self.assertAlmostEqual(123.500, rec2.import_value, places=3)
        self.assertAlmostEqual(567.900, rec2.export_value, places=3)

if __name__ == '__main__':
    unittest.main()