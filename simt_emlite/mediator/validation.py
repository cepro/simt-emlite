"""
Shared validation functions for mediator API inputs.

These functions validate input parameters without performing type conversions.
Conversion functions (e.g., string -> datetime) remain in the CLI layer (emop.py)
since the API expects typed inputs.
"""

import argparse
from decimal import Decimal


def valid_event_log_idx(idx: int) -> int:
    """
    Validate event log index is in valid range (0-9).

    Args:
        idx: Event log index

    Returns:
        The validated index

    Raises:
        ValueError: If index is out of range
    """
    if idx < 0 or idx > 9:
        raise ValueError(f"Invalid log_idx {idx}. Must be in range 0-9.")
    return idx


def valid_rate(rate: Decimal) -> Decimal:
    """
    Validate a rate value for Emlite meters.

    Rates must be:
    - Less than or equal to 1.0 GBP
    - Have at most 5 decimal places

    Args:
        rate: Rate as Decimal

    Returns:
        The validated rate

    Raises:
        ValueError: If rate is invalid
    """
    if rate > 1.0:
        raise ValueError(f"Invalid rate {rate}. Can't be greater than 1 GBP.")

    exponent_int: int = rate.as_tuple().exponent  # type: ignore[assignment]
    decimal_places = abs(exponent_int)
    if decimal_places > 5:
        raise ValueError(
            f"Invalid rate {rate}. Emlite meters can only store up to 5 decimal places."
        )

    return rate


def valid_decimal(value: Decimal) -> Decimal:
    """
    Validate that a value is a valid Decimal.

    This is a pass-through for API layer - the CLI handles string->Decimal conversion.

    Args:
        value: Decimal value

    Returns:
        The validated Decimal
    """
    return value


# CLI-specific validation functions that involve string parsing
# These are kept here for reference but may be used via argparse in emop.py


def cli_valid_event_log_idx(idx: str | None) -> int:
    """
    Parse and validate event log index from string (CLI usage).

    Args:
        idx: Event log index as string

    Returns:
        Validated integer index

    Raises:
        argparse.ArgumentTypeError: If index is invalid
    """
    if idx is None:
        raise argparse.ArgumentTypeError("event log idx cannot be None")

    try:
        idx_int = int(idx)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid log_idx {idx}. Should be an int between 0-9."
        )

    try:
        return valid_event_log_idx(idx_int)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def cli_valid_decimal(rate: str | None) -> Decimal:
    """
    Parse and validate a decimal from string (CLI usage).

    Args:
        rate: Decimal as string

    Returns:
        Validated Decimal

    Raises:
        argparse.ArgumentTypeError: If invalid
    """
    if rate is None:
        raise argparse.ArgumentTypeError("rate cannot be None")
    try:
        return Decimal(rate)
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid rate {rate}. Should be a floating point number."
        )


def cli_valid_rate(rate: str | None) -> Decimal:
    """
    Parse and validate a rate from string (CLI usage).

    Args:
        rate: Rate as string

    Returns:
        Validated Decimal rate

    Raises:
        argparse.ArgumentTypeError: If invalid
    """
    rate_decimal: Decimal = cli_valid_decimal(rate)

    try:
        return valid_rate(rate_decimal)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def cli_valid_switch(bool_str: str) -> bool:
    """
    Parse on/off string to boolean (CLI usage).

    Args:
        bool_str: "on" or "off"

    Returns:
        True for "on", False for "off"

    Raises:
        argparse.ArgumentTypeError: If invalid
    """
    bool_str_lc = bool_str.lower()
    if bool_str_lc == "on":
        return True
    elif bool_str_lc == "off":
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid flag string '{bool_str}'. Should be 'on' or 'off'."
        )
