"""
Unit tests for validation module.

Tests the shared validation functions for API inputs.
"""

import unittest
from decimal import Decimal
import argparse

from simt_emlite.mediator.validation import (
    valid_event_log_idx,
    valid_rate,
    valid_decimal,
    cli_valid_event_log_idx,
    cli_valid_decimal,
    cli_valid_rate,
    cli_valid_switch,
)


class TestValidEventLogIdx(unittest.TestCase):
    """Test valid_event_log_idx function."""

    def test_valid_idx_0(self) -> None:
        """Test that 0 is a valid index."""
        self.assertEqual(valid_event_log_idx(0), 0)

    def test_valid_idx_9(self) -> None:
        """Test that 9 is a valid index."""
        self.assertEqual(valid_event_log_idx(9), 9)

    def test_valid_idx_5(self) -> None:
        """Test that 5 is a valid index."""
        self.assertEqual(valid_event_log_idx(5), 5)

    def test_invalid_idx_negative(self) -> None:
        """Test that negative index raises ValueError."""
        with self.assertRaises(ValueError) as context:
            valid_event_log_idx(-1)
        self.assertIn("Must be in range 0-9", str(context.exception))

    def test_invalid_idx_too_high(self) -> None:
        """Test that index > 9 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            valid_event_log_idx(10)
        self.assertIn("Must be in range 0-9", str(context.exception))


class TestValidRate(unittest.TestCase):
    """Test valid_rate function."""

    def test_valid_rate_small(self) -> None:
        """Test a small valid rate."""
        rate = Decimal("0.25")
        self.assertEqual(valid_rate(rate), rate)

    def test_valid_rate_max(self) -> None:
        """Test rate at maximum (1.0)."""
        rate = Decimal("1.0")
        self.assertEqual(valid_rate(rate), rate)

    def test_valid_rate_5_decimal_places(self) -> None:
        """Test rate with exactly 5 decimal places."""
        rate = Decimal("0.23456")
        self.assertEqual(valid_rate(rate), rate)

    def test_invalid_rate_too_high(self) -> None:
        """Test that rate > 1.0 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            valid_rate(Decimal("1.01"))
        self.assertIn("greater than 1 GBP", str(context.exception))

    def test_invalid_rate_too_many_decimals(self) -> None:
        """Test that rate with >5 decimal places raises ValueError."""
        with self.assertRaises(ValueError) as context:
            valid_rate(Decimal("0.123456"))  # 6 decimal places
        self.assertIn("5 decimal places", str(context.exception))


class TestValidDecimal(unittest.TestCase):
    """Test valid_decimal function."""

    def test_valid_decimal_passthrough(self) -> None:
        """Test that valid_decimal passes through the value."""
        value = Decimal("123.45")
        self.assertEqual(valid_decimal(value), value)


class TestCliValidEventLogIdx(unittest.TestCase):
    """Test cli_valid_event_log_idx function (string parsing)."""

    def test_valid_string_idx(self) -> None:
        """Test parsing a valid string index."""
        self.assertEqual(cli_valid_event_log_idx("5"), 5)

    def test_none_raises_error(self) -> None:
        """Test that None raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_event_log_idx(None)

    def test_non_numeric_raises_error(self) -> None:
        """Test that non-numeric string raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_event_log_idx("abc")

    def test_out_of_range_raises_error(self) -> None:
        """Test that out of range value raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_event_log_idx("15")


class TestCliValidDecimal(unittest.TestCase):
    """Test cli_valid_decimal function (string parsing)."""

    def test_valid_decimal_string(self) -> None:
        """Test parsing a valid decimal string."""
        result = cli_valid_decimal("0.25")
        self.assertEqual(result, Decimal("0.25"))

    def test_none_raises_error(self) -> None:
        """Test that None raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_decimal(None)

    def test_invalid_string_raises_error(self) -> None:
        """Test that invalid string raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_decimal("not_a_number")


class TestCliValidRate(unittest.TestCase):
    """Test cli_valid_rate function (string parsing + validation)."""

    def test_valid_rate_string(self) -> None:
        """Test parsing and validating a valid rate string."""
        result = cli_valid_rate("0.25")
        self.assertEqual(result, Decimal("0.25"))

    def test_none_raises_error(self) -> None:
        """Test that None raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_rate(None)

    def test_rate_too_high_raises_error(self) -> None:
        """Test that rate > 1.0 raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_rate("1.50")


class TestCliValidSwitch(unittest.TestCase):
    """Test cli_valid_switch function."""

    def test_on_returns_true(self) -> None:
        """Test that 'on' returns True."""
        self.assertTrue(cli_valid_switch("on"))

    def test_ON_returns_true(self) -> None:
        """Test that 'ON' (uppercase) returns True."""
        self.assertTrue(cli_valid_switch("ON"))

    def test_off_returns_false(self) -> None:
        """Test that 'off' returns False."""
        self.assertFalse(cli_valid_switch("off"))

    def test_OFF_returns_false(self) -> None:
        """Test that 'OFF' (uppercase) returns False."""
        self.assertFalse(cli_valid_switch("OFF"))

    def test_invalid_value_raises_error(self) -> None:
        """Test that invalid value raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            cli_valid_switch("maybe")


if __name__ == "__main__":
    unittest.main()
