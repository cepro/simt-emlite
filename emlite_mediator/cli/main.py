import datetime
import sys
from decimal import Decimal

from emlite_mediator.mediator.client import EmliteMediatorClient
import fire

from emlite_mediator.util.logging import get_logger

logger = get_logger(__name__, __file__)


"""
    This is a CLI wrapper around the mediator client using Fire to generate the
    CLI interface from the client python interface.
"""


class EmliteMediatorCLI(EmliteMediatorClient):

    def profile_log_1_str_args(self, ts_iso_str: str):
        return self.profile_log_1(
            datetime.datetime.fromisoformat(ts_iso_str),
        )

    def profile_log_2_str_args(self, ts_iso_str: str):
        return self.profile_log_2(
            datetime.datetime.fromisoformat(ts_iso_str),
        )

    def tariffs_future_write_str_args(
        self, from_ts_iso_str: str, standing_charge_str: str, unit_rate_str: str
    ):
        self._check_amount_arg_is_string(standing_charge_str)
        self._check_amount_arg_is_string(unit_rate_str)
        self.tariffs_future_write(
            datetime.datetime.fromisoformat(from_ts_iso_str),
            standing_charge=Decimal(standing_charge_str),
            unit_rate=Decimal(unit_rate_str),
        )

    def _check_amount_arg_is_string(self, arg_value):
        if isinstance(arg_value, str):
            return
        print(
            "\nERROR: amount argument passed as floating point number. pass "
            + "as string to avoid floating point rounding errors "
            + "[eg. \"'0.234'\" or '\"0.234\"']"
        )
        sys.exit(10)


def main():
    fire.Fire(EmliteMediatorCLI)

if __name__ == "__main__":
    main()