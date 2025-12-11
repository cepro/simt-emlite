import unittest
from datetime import date, timedelta, datetime

from simt_emlite.profile_logs.group_config import GroupConfig


class TestGroupConfig(unittest.TestCase):
    """Tests for GroupConfig class, converted from Java tests."""

    DEFAULT_PROPS = {
        "overwrite": "false",
        "port": "8080",
        "prefix": "xyz",
        "devicetype": "asl",
        "startdate": "2011-11-01",
        "enddate": "2011-11-06",
    }

    GROUP_PROPS_NON_DEFAULTING = {
        "group1.folder": "downmanroad41",
        "group1.element": "A",
        "group1.host": "86.188.207.101",
    }

    def test_get_instance_from_properties_no_defaults(self):
        """Test creating GroupConfig from properties without using defaults."""
        test_props = {
            "group1.folder": "downmanroad41",
            "group1.prefix": "EML1323015436-A",
            "group1.devicetype": "asl",
            "group1.element": "A",
            "group1.startdate": "2011-08-01",
            "group1.enddate": "2011-12-06",
            "group1.overwrite": "true",
            "group1.host": "86.188.207.101",
            "group1.port": "46226",
        }

        gc = GroupConfig.get_instance_from_properties("group1", test_props, {})

        self.assertEqual(test_props["group1.folder"], str(gc.folder))
        self.assertEqual(test_props["group1.devicetype"], gc.devicetype)
        self.assertEqual(test_props["group1.prefix"], gc.prefix)
        self.assertEqual(test_props["group1.element"], gc.element)

        expected_host = test_props["group1.host"]
        expected_port = test_props["group1.port"]
        self.assertEqual(expected_host, gc.host)
        self.assertEqual(int(expected_port), gc.port)
        self.assertEqual((expected_host, int(expected_port)), gc.get_address())

        self.assertTrue(gc.overwrite)

        self.assertEqual(
            test_props["group1.startdate"],
            gc.startdate.strftime(GroupConfig.DATE_FORMAT)
        )
        self.assertEqual(
            test_props["group1.enddate"],
            gc.enddate.strftime(GroupConfig.DATE_FORMAT)
        )

        self.assertFalse(gc.test)

    def test_get_instance_from_properties_with_defaults(self):
        """Test creating GroupConfig using default values."""
        default_props = {
            "overwrite": "false",
            "port": "8080",
            "prefix": "xyz",
            "devicetype": "asl",
            "startdate": "2011-11-01",
            "enddate": "2011-11-06",
        }

        gc = GroupConfig.get_instance_from_properties(
            "group1", self.GROUP_PROPS_NON_DEFAULTING, default_props
        )

        # From defaults:
        self.assertEqual(default_props["devicetype"], gc.devicetype)
        self.assertEqual(default_props["prefix"], gc.prefix)
        self.assertEqual(
            default_props["overwrite"].lower() == "true", gc.overwrite
        )
        self.assertEqual(
            default_props["startdate"],
            gc.startdate.strftime(GroupConfig.DATE_FORMAT)
        )
        self.assertEqual(
            default_props["enddate"],
            gc.enddate.strftime(GroupConfig.DATE_FORMAT)
        )

        # From group:
        self.assertEqual(
            self.GROUP_PROPS_NON_DEFAULTING["group1.folder"], str(gc.folder)
        )
        self.assertEqual(
            self.GROUP_PROPS_NON_DEFAULTING["group1.element"], gc.element
        )

        self.assertFalse(gc.test)

        expected_host = self.GROUP_PROPS_NON_DEFAULTING["group1.host"]
        expected_port = default_props["port"]
        self.assertEqual(expected_host, gc.host)
        self.assertEqual(int(expected_port), gc.port)
        self.assertEqual((expected_host, int(expected_port)), gc.get_address())

    def test_get_instance_from_properties_with_no_default_dates(self):
        """Test creating GroupConfig when no default dates are provided."""
        default_props_no_dates = self.DEFAULT_PROPS.copy()
        del default_props_no_dates["startdate"]
        del default_props_no_dates["enddate"]

        gc = GroupConfig.get_instance_from_properties(
            "group1", self.GROUP_PROPS_NON_DEFAULTING, default_props_no_dates
        )

        # when no default date is provided start date is set to N dates in the past
        # and end date is set to today
        today = datetime.now().date()
        self.assertEqual(today - timedelta(days=30), gc.startdate)
        self.assertEqual(today, gc.enddate)

    def test_get_instance_from_properties_with_start_days(self):
        """Test creating GroupConfig with startdays property."""
        start_days = 14

        default_props_no_dates = self.DEFAULT_PROPS.copy()
        del default_props_no_dates["startdate"]
        del default_props_no_dates["enddate"]
        default_props_no_dates["startdays"] = str(start_days)

        gc = GroupConfig.get_instance_from_properties(
            "group1", self.GROUP_PROPS_NON_DEFAULTING, default_props_no_dates
        )

        # when no default date is provided start date is set to N dates in the past
        # and end date is set to today
        today = datetime.now().date()
        self.assertEqual(today - timedelta(days=start_days), gc.startdate)
        self.assertEqual(today, gc.enddate)


if __name__ == "__main__":
    unittest.main()
