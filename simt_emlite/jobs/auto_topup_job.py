import os
import sys
import traceback

from httpx import ConnectError

from simt_emlite.jobs.util import handle_supabase_faliure
from simt_emlite.util.logging import get_logger
from simt_emlite.util.supabase import supa_client

logger = get_logger(__name__, __file__)

supabase_url: str | None = os.environ.get("SUPABASE_URL")
supabase_key: str | None = os.environ.get("SUPABASE_ANON_KEY")
public_backend_role_key: str | None = os.environ.get("PUBLIC_BACKEND_ROLE_KEY")


class AutoTopupJob:
    def __init__(self):
        global logger
        self.log = logger

        self._check_environment()

        self.backend_supabase = supa_client(
            supabase_url, supabase_key, public_backend_role_key, schema="myenergy"
        )

    def run(self):
        """
        Find all meters where current balance is less than wallet minimum_balance.
        """
        self.log.info("Starting auto_topup job...")

        try:
            # Query myenergy.meters joined with myenergy.wallets
            # to find meters where balance < wallet.minimum_balance
            query_result = (
                self.backend_supabase.table("meters")
                .select(
                    """
                    id,
                    serial,
                    balance,
                    wallet,
                    wallets(id, balance, minimum_balance, target_balance, auto_topup)
                    """
                )
                .execute()
            )

            meters_needing_topup = []

            for meter in query_result.data:
                wallet = meter.get("wallets")
                if wallet is None:
                    self.log.warning(
                        "Meter has no associated wallet",
                        meter_id=meter["id"],
                        serial=meter["serial"],
                    )
                    continue

                meter_balance = meter.get("balance")
                wallet_minimum = wallet.get("minimum_balance")
                auto_topup_enabled = wallet.get("auto_topup")

                # Check if meter balance is below wallet minimum_balance
                if meter_balance is not None and meter_balance < wallet_minimum:
                    if auto_topup_enabled:
                        meters_needing_topup.append(
                            {
                                "meter_id": meter["id"],
                                "serial": meter["serial"],
                                "meter_balance": meter_balance,
                                "wallet_id": wallet["id"],
                                "wallet_minimum_balance": wallet_minimum,
                                "wallet_target_balance": wallet.get("target_balance"),
                                "wallet_current_balance": wallet.get("balance"),
                            }
                        )
                        self.log.info(
                            "Meter needs topup",
                            meter_id=meter["id"],
                            serial=meter["serial"],
                            meter_balance=meter_balance,
                            wallet_minimum_balance=wallet_minimum,
                        )
                    else:
                        self.log.info(
                            "Meter below minimum but auto_topup disabled",
                            meter_id=meter["id"],
                            serial=meter["serial"],
                            meter_balance=meter_balance,
                            wallet_minimum_balance=wallet_minimum,
                        )

            self.log.info(
                f"Found {len(meters_needing_topup)} meters needing topup",
                count=len(meters_needing_topup),
            )

            # Output results
            print("\n=== METERS NEEDING TOPUP ===")
            for meter in meters_needing_topup:
                print(f"\nMeter ID: {meter['meter_id']}")
                print(f"  Serial: {meter['serial']}")
                print(f"  Meter Balance: {meter['meter_balance']}")
                print(f"  Wallet ID: {meter['wallet_id']}")
                print(f"  Wallet Minimum Balance: {meter['wallet_minimum_balance']}")
                print(f"  Wallet Target Balance: {meter['wallet_target_balance']}")
                print(f"  Wallet Current Balance: {meter['wallet_current_balance']}")

            print(f"\nTotal meters needing topup: {len(meters_needing_topup)}")
            print("=== END RESULTS ===\n")

        except ConnectError as e:
            handle_supabase_faliure(self.log, e)
            sys.exit(5)
        except Exception as e:
            self.log.error(
                "Failure occurred during auto_topup job",
                error=e,
                exception=traceback.format_exception(e),
            )
            sys.exit(6)

    def _check_environment(self):
        if not supabase_url or not supabase_key:
            self.log.error(
                "Environment variables SUPABASE_URL and SUPABASE_ANON_KEY not set."
            )
            sys.exit(2)

        if not public_backend_role_key:
            self.log.error("Environment variable PUBLIC_BACKEND_ROLE_KEY not set.")
            sys.exit(3)


if __name__ == "__main__":
    runner = AutoTopupJob()
    runner.run()
