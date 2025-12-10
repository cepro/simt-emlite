#!/usr/bin/env python3
"""
Test cases for SMIPFileFinder based on Java SMIPFileFinderTest class
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from simt_emlite.smip.smip_filename import SMIPFilename, ElementMarker
from simt_emlite.smip.smip_file_finder import SMIPFileFinder

class TestSMIPFileFinder(unittest.TestCase):
    """Test cases for SMIPFileFinder"""

    def setUp(self):
        """Set up test fixtures"""
        self.PREFIX = "EML1112223334"
        self.DATE = date(2020, 1, 1)
        self.DATE_FORMATTED = self.DATE.strftime('%Y%m%d')

        self.filename_no_el = SMIPFilename(self.PREFIX, self.DATE)
        self.filename_el_a = SMIPFilename(self.PREFIX, self.DATE, ElementMarker.A)
        self.filename_el_b = SMIPFilename(self.PREFIX, self.DATE, ElementMarker.B)

        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory and all contents
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_find_ingested_simtricity(self):
        """Test finding a file that has been ingested into Simtricity"""
        test_folder = Path(self.temp_dir) / "test_ingested_simtricity"
        test_folder.mkdir()

        # Create test file with Simtricity ingestion marker
        test_file = test_folder / self.filename_no_el.filename(ingested_simtricity=True, ingested_timescale=False)
        test_file.touch()

        result = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)

        self.assertTrue(result.found)
        self.assertTrue(result.ingested_simtricity)
        self.assertTrue(result.ingested())
        self.assertFalse(result.ingested_timescale)
        self.assertEqual(str(test_file.absolute()), str(result.smip_file.absolute()))

    def test_find_not_ingested(self):
        """Test finding a file that has not been ingested"""
        test_folder = Path(self.temp_dir) / "test_not_ingested"
        test_folder.mkdir()

        # Create test file without ingestion markers
        test_file = test_folder / self.filename_no_el.filename(ingested_simtricity=False, ingested_timescale=False)
        test_file.touch()

        result = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)

        self.assertTrue(result.found)
        self.assertFalse(result.ingested())
        self.assertFalse(result.ingested_simtricity)
        self.assertFalse(result.ingested_timescale)
        self.assertEqual(str(test_file.absolute()), str(result.smip_file.absolute()))

    def test_find_ingested_both(self):
        """Test finding a file that has been ingested into both systems"""
        test_folder = Path(self.temp_dir) / "test_ingested_both"
        test_folder.mkdir()

        # Create test file with both ingestion markers
        test_file = test_folder / self.filename_no_el.filename(ingested_simtricity=True, ingested_timescale=True)
        test_file.touch()

        result = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)

        self.assertTrue(result.found)
        self.assertTrue(result.ingested())
        self.assertTrue(result.ingested_simtricity)
        self.assertTrue(result.ingested_timescale)
        self.assertEqual(str(test_file.absolute()), str(result.smip_file.absolute()))

    def test_find_with_element_a(self):
        """Test finding a file with element marker A"""
        test_folder = Path(self.temp_dir) / "test_element_a"
        test_folder.mkdir()

        # Create test file with element A
        test_file = test_folder / self.filename_el_a.filename(ingested_simtricity=False, ingested_timescale=False)
        test_file.touch()

        result = SMIPFileFinder.find_with_element(
            test_folder,
            self.PREFIX,
            self.DATE,
            ElementMarker.A
        )

        self.assertTrue(result.found)
        self.assertFalse(result.ingested())
        self.assertFalse(result.ingested_simtricity)
        self.assertFalse(result.ingested_timescale)
        self.assertEqual(str(test_file.absolute()), str(result.smip_file.absolute()))

    def test_find_not_exists(self):
        """Test finding a file that doesn't exist"""
        test_folder = Path(self.temp_dir) / "test_not_exists"
        test_folder.mkdir()

        # Test with no file
        result_no_file = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)
        self.assertFalse(result_no_file.found)
        self.assertFalse(result_no_file.ingested())
        self.assertFalse(result_no_file.ingested_simtricity)
        self.assertFalse(result_no_file.ingested_timescale)
        self.assertIsNone(result_no_file.smip_file)

        # Test with file for another day but not for the searched day
        filename_other_day = SMIPFilename(self.PREFIX, self.DATE.replace(day=2))
        test_file = test_folder / filename_other_day.filename(ingested_simtricity=True, ingested_timescale=True)
        test_file.touch()

        result_no_file_for_day = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)
        self.assertFalse(result_no_file_for_day.found)
        self.assertFalse(result_no_file_for_day.ingested())
        self.assertFalse(result_no_file_for_day.ingested_simtricity)
        self.assertFalse(result_no_file_for_day.ingested_timescale)
        self.assertIsNone(result_no_file_for_day.smip_file)

    def test_find_element(self):
        """Test finding a file with element marker"""
        test_folder = Path(self.temp_dir) / "test_element"
        test_folder.mkdir()

        # Create test file without element marker
        test_file = test_folder / self.filename_no_el.filename(ingested_simtricity=False, ingested_timescale=False)
        test_file.touch()

        result = SMIPFileFinder.find(test_folder, self.PREFIX, self.DATE)

        self.assertTrue(result.found)
        self.assertEqual(str(test_file.absolute()), str(result.smip_file.absolute()))

        self.assertFalse(result.ingested())
        self.assertFalse(result.ingested_simtricity)
        self.assertFalse(result.ingested_timescale)

    def test_find_downloaded(self):
        """Test finding downloaded files (not ingested)"""
        test_folder = Path(self.temp_dir) / "test_downloaded"
        test_folder.mkdir()

        # Add a mix of files - ingested / not ingested, with / without element
        file_no_el_no_ingest = test_folder / self.filename_no_el.filename(False, False)
        file_el_a_no_ingest = test_folder / self.filename_el_a.filename(False, False)
        file_el_b_no_ingest = test_folder / self.filename_el_b.filename(False, False)
        file_no_el_ingest = test_folder / self.filename_no_el.filename(True, False)
        file_el_a_ingest = test_folder / self.filename_el_a.filename(False, True)
        file_el_b_ingest = test_folder / self.filename_el_b.filename(True, True)

        file_no_el_no_ingest.touch()
        file_el_a_no_ingest.touch()
        file_el_b_no_ingest.touch()
        file_no_el_ingest.touch()
        file_el_a_ingest.touch()
        file_el_b_ingest.touch()

        files = SMIPFileFinder.find_downloaded(test_folder)

        self.assertEqual(3, len(files))

        expected_matches = [
            file_no_el_no_ingest,
            file_el_a_no_ingest,
            file_el_b_no_ingest
        ]

        for expected_file in expected_matches:
            found = any(str(f.absolute()) == str(expected_file.absolute()) for f in files)
            self.assertTrue(found, f"Expected file {expected_file} not found in results")

if __name__ == '__main__':
    unittest.main()