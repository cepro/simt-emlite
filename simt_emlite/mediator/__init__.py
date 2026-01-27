"""
Mediator module for Emlite meter communication.

This module provides the API clients for interacting with Emlite meters
through the mediator service.

Available clients:
- EmliteMediatorAPI: Core meter operations (from api_core)
- EmlitePrepayAPI: Prepay and tariff operations (from api_prepay)
- EmliteMeterManagementAPI: Meter management operations (from api_management)

For backward compatibility, EmliteMediatorAPI is also available as the
main import from this module.
"""

from .api_core import EmliteMediatorAPI
from .api_management import EmliteMeterManagementAPI, MeterClockDriftInfo
from .api_prepay import EmlitePrepayAPI, PricingTable, TariffsActive, TariffsFuture

__all__ = [
    "EmliteMediatorAPI",
    "EmliteMeterManagementAPI",
    "EmlitePrepayAPI",
    "MeterClockDriftInfo",
    "PricingTable",
    "TariffsActive",
    "TariffsFuture",
]
