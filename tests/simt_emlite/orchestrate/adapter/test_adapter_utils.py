#!/usr/bin/env python3
import unittest
from simt_emlite.orchestrate.adapter.adapter_utils import build_app_name


class TestBuildAppName(unittest.TestCase):
    """Test cases for build_app_name function"""

    def test_single_meter_app_with_prod_env(self):
        """Test single meter app with prod environment

        Note: The condition (env is not None or env != "prod" and env != "qa")
        always evaluates to True due to operator precedence, so env_part is
        always set to "-{env}" when env is provided.
        """
        result = build_app_name(is_single_meter_app=True, serial="ABC123", esco="ESCO001", env="prod")
        self.assertEqual("mediator-abc123", result)

    def test_single_meter_app_with_qa_env(self):
        """Test single meter app with qa environment"""
        result = build_app_name(is_single_meter_app=True, serial="XYZ789", esco="ESCO002", env="qa")
        self.assertEqual("mediator-xyz789", result)

    def test_single_meter_app_with_dev_env(self):
        """Test single meter app with dev environment"""
        result = build_app_name(is_single_meter_app=True, serial="DEV456", esco="ESCO003", env="dev")
        self.assertEqual("mediator-dev-dev456", result)

    def test_multi_meter_app_with_prod_env(self):
        """Test multi meter app with prod environment"""
        result = build_app_name(is_single_meter_app=False, serial="MULTI001", esco="ESCO005", env="prod")
        self.assertEqual("mediators-esco005", result)

    def test_multi_meter_app_with_qa_env(self):
        """Test multi meter app with qa environment"""
        result = build_app_name(is_single_meter_app=False, serial="MULTI002", esco="ESCO006", env="qa")
        self.assertEqual("mediators-esco006", result)

    def test_multi_meter_app_with_dev_env(self):
        """Test multi meter app with dev environment"""
        result = build_app_name(is_single_meter_app=False, serial="MULTI003", esco="ESCO007", env="dev")
        self.assertEqual("mediators-dev-esco007", result)

if __name__ == "__main__":
    unittest.main()
