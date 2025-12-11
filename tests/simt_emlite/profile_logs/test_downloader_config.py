import unittest
from datetime import date, timedelta, datetime
from pathlib import Path

from simt_emlite.profile_logs.downloader_config import DownloaderConfig, ConfigException


class TestDownloaderConfig(unittest.TestCase):
    """Tests for DownloaderConfig class, converted from Java tests."""

    GROUP1 = "downmanroad41"
    GROUP2 = "downmanroad88"

    @staticmethod
    def get_config_properties_with_2_groups():
        return {
            "rootfolder": "/tmp/downloads",
            "sleepseconds": "10",
            "testmode": "no",
            # Group 1
            "downmanroad41.folder": "downmanroad41",
            "downmanroad41.port": "46226",
            "downmanroad41.prefix": "EML1323015436-A",
            "downmanroad41.devicetype": "asl",
            "downmanroad41.element": "A",
            "downmanroad41.host": "86.188.207.101",
            "downmanroad41.startdate": "2011-08-01",
            "downmanroad41.enddate": "2011-12-06",
            "downmanroad41.overwrite": "true",
            # Group 2
            "downmanroad88.folder": "downmanroad88",
            "downmanroad88.port": "46227",
            "downmanroad88.prefix": "EML1323015437-B",
            "downmanroad88.devicetype": "asl",
            "downmanroad88.element": "B",
            "downmanroad88.host": "86.188.207.102",
            "downmanroad88.startdate": "2011-08-01",
            "downmanroad88.enddate": "2011-12-06",
            "downmanroad88.overwrite": "false",
        }

    @staticmethod
    def get_config_properties_with_defaults():
        """Equivalent of Java getConfigProperties("with_defaults")."""
        return {
            "rootfolder": "/tmp/downloads",
            "sleepseconds": "10",
            # Default properties
            "default.port": "8080",
            "default.prefix": "xyz",
            "default.overwrite": "false",
            "default.startdays": "14",
            "default.devicetype": "asl",
            # Group 1 - only partial properties, rest from defaults
            "downmanroad41.folder": "downmanroad41",
            "downmanroad41.element": "A",
            "downmanroad41.host": "86.188.207.101",
        }

    def test_load_config_with_two_groups(self):
        """Test loading config with two groups."""
        config_props = self.get_config_properties_with_2_groups()
        dc = DownloaderConfig(config_props)

        self.assertEqual(
            config_props[DownloaderConfig.PROPERTY_ROOT_FOLDER],
            str(dc.get_root_folder())
        )

        self.assertEqual(
            int(config_props[DownloaderConfig.PROPERTY_SLEEPSECONDS]),
            dc.get_sleep_seconds()
        )

        groups = dc.get_groups()
        group_names = groups.keys()
        self.assertIn(self.GROUP1, group_names)
        self.assertIn(self.GROUP2, group_names)

        group1 = groups[self.GROUP1]
        self.assertEqual(self.GROUP1, str(group1.folder))
        self.assertEqual(int(config_props[f"{self.GROUP1}.port"]), group1.port)
        self.assertEqual(config_props[f"{self.GROUP1}.prefix"], group1.prefix)

        group2 = groups[self.GROUP2]
        self.assertEqual(self.GROUP2, str(group2.folder))
        self.assertEqual(int(config_props[f"{self.GROUP2}.port"]), group2.port)
        self.assertEqual(config_props[f"{self.GROUP2}.prefix"], group2.prefix)

    def test_load_config_with_defaults(self):
        """Test loading config using default values."""
        config_props = self.get_config_properties_with_defaults()
        dc = DownloaderConfig(config_props)

        self.assertEqual(
            config_props[DownloaderConfig.PROPERTY_ROOT_FOLDER],
            str(dc.get_root_folder())
        )

        groups = dc.get_groups()
        group = groups[self.GROUP1]

        #
        # Check properties set by defaults
        #
        self.assertEqual(int(config_props["default.port"]), group.port)
        self.assertEqual(config_props["default.prefix"], group.prefix)
        self.assertEqual(
            config_props["default.overwrite"].lower() == "true",
            group.overwrite
        )

        # startdate derived from default.startdays
        start_days = int(config_props["default.startdays"])
        expected_start_date = datetime.now().date() - timedelta(days=start_days)
        self.assertEqual(expected_start_date, group.startdate)

        # enddate defaults to today
        self.assertEqual(datetime.now().date(), group.enddate)

        #
        # Check properties set explicitly
        #
        self.assertEqual(self.GROUP1, group.folder.name)
        self.assertEqual(config_props[f"{self.GROUP1}.element"], group.element)
        self.assertEqual(config_props[f"{self.GROUP1}.host"], group.host)

    def test_empty_root_folder_throws(self):
        """Test that missing root folder raises ConfigException."""
        config_props = {}
        with self.assertRaises(ConfigException) as context:
            DownloaderConfig(config_props)

        self.assertEqual(
            "no rootfolder property set - specify a rootfolder to download the files to",
            str(context.exception)
        )

    def test_defaults(self):
        """Test default values for sleepseconds and testmode."""
        config_props = self.get_config_properties_with_2_groups()
        del config_props["sleepseconds"]
        if "testmode" in config_props:
            del config_props["testmode"]

        dc = DownloaderConfig(config_props)
        self.assertEqual(5, dc.get_sleep_seconds())
        self.assertFalse(dc.get_test_mode())

    def test_get_defaults_from_properties(self):
        """Test extracting default properties."""
        props = {
            "default.overwrite": "false",
            "default.prefix": "xyz",
            "other.non.default": "abc",
        }

        default_props = DownloaderConfig.defaults_from_properties(props)
        self.assertEqual(2, len(default_props))
        self.assertEqual("xyz", default_props["prefix"])
        self.assertEqual("false", default_props["overwrite"])


if __name__ == "__main__":
    unittest.main()
