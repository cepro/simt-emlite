import traceback
from datetime import datetime, timezone
from decimal import Decimal

from simt_emlite.mediator.client import EmliteMediatorClient, MediatorClientException
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import Client as SupabaseClient

logger = get_logger(__name__, __file__)


class FutureTariffsUpdateJob:
    def __init__(
        self,
        *,
        tariff: str,
        mediator_address: str,
        supabase: SupabaseClient,
    ):
        self.tariff = tariff
        self.mediator_address = mediator_address
        self.supabase = supabase

        self.emlite_client = EmliteMediatorClient(
            mediator_address=mediator_address,
            meter_id=tariff["meter_id"],
        )

        global logger
        self.log = logger.bind(
            serial=tariff["serial"],
            meter_id=tariff["meter_id"],
            mediator_address=mediator_address,
        )

    def update(self) -> bool:
        """
        Update the future tariff on the meter.
        Returns True if successful, False if failed.
        """

        try:
            self.emlite_client.tariffs_future_write(
                datetime.strptime(
                    self.tariff["tariff_period_start"], "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc),
                # should be Decimals already but lets convert to be sure
                # important to wrap in str() first to avoid floating point rounding issues
                Decimal(str(self.tariff["customer_standing_charge"])),
                Decimal(str(self.tariff["customer_unit_rate"])),
                Decimal(str(self.tariff["emergency_credit"])),
                Decimal(str(self.tariff["ecredit_button_threshold"])),
                Decimal(str(self.tariff["debt_recovery_rate"])),
            )
            self.log.info("future tariff set")
            return True
        except MediatorClientException as e:
            self.log.error(
                "Mediator client failure",
                error=e,
                exception=traceback.format_exception(e),
            )
        except Exception as e:
            self.log.error(
                "Unknown failure during future tariff update",
                error=e,
                exception=traceback.format_exception(e),
            )

        return False
