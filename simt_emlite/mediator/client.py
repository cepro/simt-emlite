"""
Backward compatibility module.

This module re-exports EmliteMediatorAPI from api_core for backward compatibility.
New code should import directly from api_core or api_prepay.

Deprecated: Import from simt_emlite.mediator instead.
"""

import warnings

from .api_core import EmliteMediatorAPI
from .api_prepay import (
    EmlitePrepayAPI,
    PricingTable,
    TariffsActive,
    TariffsFuture,
)

# Issue deprecation warning on import
warnings.warn(
    "Importing from simt_emlite.mediator.client is deprecated. "
    "Use simt_emlite.mediator.api_core or simt_emlite.mediator.api_prepay instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "EmliteMediatorAPI",
    "EmlitePrepayAPI",
    "PricingTable",
    "TariffsActive",
    "TariffsFuture",
]
