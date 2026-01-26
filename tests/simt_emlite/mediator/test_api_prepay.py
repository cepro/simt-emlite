"""
Unit tests for api_prepay module.

Tests the prepay and tariff API functions with mocked gRPC responses.
"""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestPrepayBalance(unittest.TestCase):
    """Test prepay_balance parses balance from response."""

    @patch("simt_emlite.mediator.api_core.EmliteMediatorGrpcClient")
    def test_prepay_balance_returns_scaled_decimal(
        self, mock_grpc_client_class: MagicMock
    ) -> None:
        """Test that prepay_balance correctly scales and returns the balance."""
        from simt_emlite.mediator.api_prepay import EmlitePrepayAPI

        # Raw balance value (in internal units - needs to be scaled by /100000)
        # e.g., 1500000 raw = £15.00
        mock_response = MagicMock()
        mock_response.balance = 1500000

        mock_grpc_instance = MagicMock()
        mock_grpc_instance.read_element.return_value = mock_response
        mock_grpc_client_class.return_value = mock_grpc_instance

        client = EmlitePrepayAPI(mediator_address="test:50051")
        result = client.prepay_balance("EML123456789")

        # emop_scale_price_amount divides by 100000
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal("15.00000"))


if __name__ == "__main__":
    unittest.main()
