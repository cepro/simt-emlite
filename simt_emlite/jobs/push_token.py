import datetime
import traceback
from decimal import Decimal
from typing import Optional

from httpx import ConnectError

from simt_emlite.jobs.util import handle_supabase_faliure
from simt_emlite.mediator.client import EmliteMediatorClient, MediatorClientException
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import Client as SupabaseClient

logger = get_logger(__name__, __file__)


class PushTokenJob:
    def __init__(
        self,
        *,
        topup_id: str,
        meter_id: str,
        token: str,
        mediator_address: str,
        supabase: SupabaseClient,
    ):
        self.topup_id = topup_id
        self.meter_id = meter_id
        self.token = token
        self.mediator_address = mediator_address
        self.supabase = supabase

        self.emlite_client = EmliteMediatorClient(
            mediator_address=mediator_address,
            meter_id=meter_id,
        )

        global logger
        self.log = logger.bind(
            topup_id=topup_id,
            meter_id=meter_id,
            mediator_address=mediator_address
        )

    def push(self) -> bool:
        """
        Push a token to a meter and verify balance increase.
        Returns True if successful, False if failed.
        """
        try:
            # Check initial balance
            initial_balance = self._check_balance()
            if initial_balance is None:
                return self._update_status("failed_token_push", "Failed to check initial balance")

            self.log.info("Initial balance checked", balance=initial_balance)

            # Send token
            self._send_token()
            self.log.info("Token sent", token=self.token)

            # Check balance after token push
            updated_balance = self._check_balance()
            if updated_balance is None:
                return self._update_status("failed_token_push", "Failed to check updated balance")

            self.log.info("Updated balance checked", balance=updated_balance)

            # Verify balance increased
            if updated_balance <= initial_balance:
                return self._update_status(
                    "failed_token_push", 
                    f"Balance did not increase: {initial_balance} -> {updated_balance}"
                )

            # Success - update topup as used
            return self._update_status(
                "token_pushed", 
                f"Balance increased: {initial_balance} -> {updated_balance}",
                True
            )

        except MediatorClientException as e:
            self.log.error(
                "Mediator client failure",
                error=e,
                exception=traceback.format_exception(e),
            )
            return self._update_status("failed_token_push", f"Mediator error: {e.message}")
        except Exception as e:
            self.log.error(
                "Unknown failure during token push",
                error=e,
                exception=traceback.format_exception(e),
            )
            return self._update_status("failed_token_push", f"Error: {str(e)}")

    def _check_balance(self) -> Optional[Decimal]:
        """Check and return the current prepay balance."""
        try:
            return self.emlite_client.prepay_balance()
        except Exception as e:
            self.log.error(
                "Failed to check balance",
                error=e,
                exception=traceback.format_exception(e),
            )
            return None

    def _send_token(self):
        """Send the token to the meter."""
        self.emlite_client.prepay_send_token(self.token)

    def _update_status(self, status: str, notes: str, mark_used=False) -> bool:
        """
        Update the topup status in the database.
        Returns True if operation was successful, False otherwise.
        """
        try:
            update_data = {
                "status": status,
                "notes": notes,
                "updated_at": datetime.datetime.now().isoformat(),
            }
            
            if mark_used:
                update_data["used_at"] = datetime.datetime.now().isoformat()

            self.supabase.table("topups").update(update_data).eq("id", self.topup_id).execute()
            
            self.log.info(
                "Updated topup status",
                topup_id=self.topup_id,
                status=status,
                notes=notes,
            )
            return status == "token_pushed"
        except ConnectError as e:
            handle_supabase_faliure(self.log, e)
            return False