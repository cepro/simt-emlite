#!/usr/bin/env python3
"""
Unit tests for SMIPFilename class based on Java SMIPFilenameTest
"""

import unittest
from datetime import date
from simt_emlite.smip.smip_filename import SMIPFilename, ElementMarker, IngestionMarker

class TestSMIPFilename(unittest.TestCase):

    def setUp(self):
        self.PREFIX = "EML1112223334"
        self.DATE = date(2020, 1, 1)
        self.DATE_FORMATTED = self.DATE.strftime('%Y%m%d')

        self.filename_no_el = SMIPFilename(self.PREFIX, self.DATE)
        self.filename_el_a = SMIPFilename(self.PREFIX, self.DATE, ElementMarker.A)
        self.filename_el_b = SMIPFilename(self.PREFIX, self.DATE, ElementMarker.B)

    def test_constructed_by_details(self):
        self.assertEqual(self.PREFIX, self.filename_no_el.get_prefix())
        self.assertEqual(self.PREFIX, self.filename_el_a.get_prefix())
        self.assertEqual(self.PREFIX, self.filename_el_b.get_prefix())

        self.assertEqual(self.DATE, self.filename_no_el.get_day())
        self.assertEqual(self.DATE, self.filename_el_a.get_day())
        self.assertEqual(self.DATE, self.filename_el_b.get_day())

        self.assertIsNone(self.filename_no_el.get_element_marker())
        self.assertEqual(ElementMarker.A, self.filename_el_a.get_element_marker())
        self.assertEqual(ElementMarker.B, self.filename_el_b.get_element_marker())

    def test_constructed_by_full_filename(self):
        """Test construction by full filename parsing"""
        # Test with all markers
        file_set_all = f"{self.PREFIX}-A-{self.DATE_FORMATTED}_st.csv"
        smip_filename1 = SMIPFilename.from_filename(file_set_all)

        self.assertEqual(self.PREFIX, smip_filename1.get_prefix())
        self.assertEqual(self.DATE, smip_filename1.get_day())
        self.assertEqual(ElementMarker.A, smip_filename1.get_element_marker())
        self.assertTrue(smip_filename1.is_ingested_simtricity())
        self.assertTrue(smip_filename1.is_ingested_timescale())

        # Test with partial markers
        file_set_partial = f"{self.PREFIX}-{self.DATE_FORMATTED}_t.csv"
        smip_filename2 = SMIPFilename.from_filename(file_set_partial)

        self.assertEqual(self.PREFIX, smip_filename2.get_prefix())
        self.assertEqual(self.DATE, smip_filename2.get_day())
        self.assertIsNone(smip_filename2.get_element_marker())
        self.assertFalse(smip_filename2.is_ingested_simtricity())
        self.assertTrue(smip_filename2.is_ingested_timescale())

    def test_ingestion_markers(self):
        """Test ingestion markers in filenames"""
        expected_prefix = f"{self.PREFIX}-{self.DATE_FORMATTED}"

        self.assertEqual(f"{expected_prefix}_s.csv", self.filename_no_el.filename(ingested_simtricity=True, ingested_timescale=False))
        self.assertEqual(f"{expected_prefix}_t.csv", self.filename_no_el.filename(ingested_simtricity=False, ingested_timescale=True))
        self.assertEqual(f"{expected_prefix}_st.csv", self.filename_no_el.filename(ingested_simtricity=True, ingested_timescale=True))
        self.assertEqual(f"{expected_prefix}.csv", self.filename_no_el.filename(ingested_simtricity=False, ingested_timescale=False))

    def test_element_markers(self):
        """Test element markers in filenames"""
        self.assertEqual(
            f"{self.PREFIX}-{ElementMarker.A.value}-{self.DATE_FORMATTED}.csv",
            self.filename_el_a.filename(ingested_simtricity=False, ingested_timescale=False)
        )
        self.assertEqual(
            f"{self.PREFIX}-{ElementMarker.B.value}-{self.DATE_FORMATTED}.csv",
            self.filename_el_b.filename(ingested_simtricity=False, ingested_timescale=False)
        )

    def test_combination(self):
        """Test combination of element and ingestion markers"""
        self.assertEqual(
            f"{self.PREFIX}-{ElementMarker.A.value}-{self.DATE_FORMATTED}_"
            f"{IngestionMarker.SIMTRICITY.value}{IngestionMarker.TIMESCALE.value}.csv",
            self.filename_el_a.filename(ingested_simtricity=True, ingested_timescale=True)
        )

    def test_get_serial_and_day_prefix(self):
        """Test serial_element_day_prefix method"""
        self.assertEqual(f"{self.PREFIX}-{self.DATE_FORMATTED}", self.filename_no_el.serial_element_day_prefix())
        self.assertEqual(
            f"{self.PREFIX}-{ElementMarker.A.value}-{self.DATE_FORMATTED}",
            self.filename_el_a.serial_element_day_prefix()
        )

    def test_filename_parsing_edge_cases(self):
        """Test edge cases for filename parsing"""
        # Test basic filename without any markers
        basic_filename = f"{self.PREFIX}-{self.DATE_FORMATTED}.csv"
        parsed_basic = SMIPFilename.from_filename(basic_filename)

        self.assertEqual(self.PREFIX, parsed_basic.get_prefix())
        self.assertEqual(self.DATE, parsed_basic.get_day())
        self.assertIsNone(parsed_basic.get_element_marker())
        self.assertFalse(parsed_basic.is_ingested_simtricity())
        self.assertFalse(parsed_basic.is_ingested_timescale())

        # Test filename with only simtricity marker
        simtricity_only = f"{self.PREFIX}-{self.DATE_FORMATTED}_s.csv"
        parsed_simtricity = SMIPFilename.from_filename(simtricity_only)

        self.assertTrue(parsed_simtricity.is_ingested_simtricity())
        self.assertFalse(parsed_simtricity.is_ingested_timescale())

    def test_invalid_filename_format(self):
        """Test that invalid filenames raise ValueError"""
        invalid_filenames = [
            "invalid_filename.csv",
            "EML123-20200101.txt",  # wrong extension
            "EML123-20200101",     # no extension
            "EML123-20200101_x.csv", # invalid ingestion marker
        ]

        for invalid_filename in invalid_filenames:
            with self.subTest(filename=invalid_filename):
                with self.assertRaises(ValueError):
                    SMIPFilename.from_filename(invalid_filename)

if __name__ == "__main__":
    unittest.main()