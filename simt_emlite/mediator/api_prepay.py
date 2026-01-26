# mypy: disable-error-code="import-untyped"
"""
Prepay and Tariff API for Emlite meter operations.

This module provides the API for prepay mode operations, balance management,
token handling, and tariff configuration.
"""
import datetime
from decimal import Decimal
from typing import Any, Dict, List, TypedDict, cast

from emop_frame_protocol.emop_message import EmopMessage
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.util import (
    emop_encode_amount_as_u4le_rec,
    emop_encode_timestamp_as_u4le_rec,
    emop_epoch_seconds_to_datetime,
    emop_scale_price_amount,
)

from .api_core import EmliteMediatorClient


# 8 blocks x 8 rates for tariff pricings
PricingTable = List[List[Decimal]]


class TariffsActive(TypedDict):
    standing_charge: str

    unit_rate_element_a: str
    unit_rate_element_b: str

    threshold_mask: Dict[str, int]
    threshold_values: Dict[str, bool]

    price_current: Decimal | None
    price_index_current: int | None
    tou_rate: int | None
    block_rate: int | None

    prepayment_emergency_credit: str
    prepayment_ecredit_availability: str
    prepayment_debt_recovery_rate: str

    gas: Decimal | None

    element_b_tou_rate: int
    element_b_block_rate: int | None
    element_b_price_index_current: int | None

    element_b_tou_rate_1: Decimal | None
    element_b_tou_rate_2: Decimal | None
    element_b_tou_rate_3: Decimal | None
    element_b_tou_rate_4: Decimal | None

    pricings: PricingTable | None


class TariffsFuture(TypedDict):
    standing_charge: str

    unit_rate_element_a: str
    unit_rate_element_b: str

    threshold_mask: Dict[str, int]
    threshold_values: Dict[str, bool]

    activation_datetime: datetime.datetime

    prepayment_emergency_credit: str
    prepayment_ecredit_availability: str
    prepayment_debt_recovery_rate: str

    element_b_tou_rate_1: Decimal | None
    element_b_tou_rate_2: Decimal | None
    element_b_tou_rate_3: Decimal | None
    element_b_tou_rate_4: Decimal | None

    pricings: PricingTable | None


class EmlitePrepayClient(EmliteMediatorClient):
    """
    API client for Emlite prepay and tariff operations.

    Extends EmliteMediatorClient with prepay mode management, balance operations,
    token handling, and tariff configuration methods.
    """

    def prepay_enabled(self, serial: str) -> bool:
        data = self._read_element(serial, ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received prepay enabled flag", prepay_enabled_flag=enabled, serial=serial
        )
        return enabled

    def prepay_no_debt_recovery_when_emergency_credit_enabled(
        self, serial: str
    ) -> bool:
        data = self._read_element(
            serial, ObjectIdEnum.prepay_no_debt_recovery_when_emergency_credit_flag
        )
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received no debt recovery when in emergency credit flag",
            prepay_no_debt_recovery_when_emergency_credit_flag=enabled,
            serial=serial,
        )
        return enabled

    def prepay_no_standing_charge_when_power_fail_enabled(self, serial: str) -> bool:
        data = self._read_element(
            serial, ObjectIdEnum.prepay_no_standing_charge_when_power_fail_flag
        )
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received no standing charge when power fail flag",
            prepay_no_standing_charge_when_power_fail_flag=enabled,
            serial=serial,
        )
        return enabled

    def prepay_enabled_write(self, serial: str, enabled: bool) -> None:
        if enabled:
            balance_gbp = self.prepay_balance(serial)
            if balance_gbp < 10.0:
                raise Exception(
                    f"balance {balance_gbp} too low to enable prepay mode (< 10.0). add more credit and try again."
                )
        flag_bytes = bytes.fromhex("01" if enabled else "00")
        self._write_element(serial, ObjectIdEnum.prepay_enabled_flag, flag_bytes)

    def prepay_balance(self, serial: str) -> Decimal:
        data = self._read_element(serial, ObjectIdEnum.prepay_balance)
        self.log.debug(
            "received prepay balance", prepay_balance_raw=data.balance, serial=serial
        )
        balance_gbp: Decimal = emop_scale_price_amount(Decimal(data.balance))
        self.log.info(
            "prepay balance in GBP", prepay_balance_gbp=balance_gbp, serial=serial
        )
        return balance_gbp

    def prepay_send_token(self, serial: str, token: str) -> None:
        token_bytes = token.encode("ascii")
        self._write_element(serial, ObjectIdEnum.prepay_token_send, token_bytes)

    def prepay_transaction_count(self, serial: str) -> int:
        data = self._read_element(serial, ObjectIdEnum.monetary_info_transaction_count)
        self.log.info(
            "received prepay transaction count",
            transaction_count=data.count,
            serial=serial,
        )
        return cast(int, data.count)

    def tariffs_active_read(self, serial: str) -> TariffsActive:
        standing_charge_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_standing_charge
        )
        self.log.debug(
            "standing charge", value=standing_charge_rec.value, serial=serial
        )

        threshold_mask_rec: EmopMessage.TariffThresholdMaskRec = self._read_element(
            serial, ObjectIdEnum.tariff_active_threshold_mask
        )
        threshold_values_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_threshold_values
        )
        self._log_thresholds(threshold_mask_rec, threshold_values_rec)

        block_8_rate_1_price_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_block_8_rate_1
        )
        self.log.debug(
            "block 8 rate 1 (element a activated rate)",
            value=emop_scale_price_amount(block_8_rate_1_price_rec.value),
            serial=serial,
        )

        active_price_rec = self._read_element(serial, ObjectIdEnum.tariff_active_price)
        self.log.debug(
            "element a unit rate (active a price)",
            value=active_price_rec.value,
            serial=serial,
        )

        block_rate_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_block_rate
        )
        self.log.debug(
            "element a block rate index (0-7)",
            value=block_rate_rec.value,
            serial=serial,
        )

        tou_rate_index_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_tou_rate
        )
        self.log.debug(
            "element a tou rate index (0-7)",
            value=tou_rate_index_rec.value,
            serial=serial,
        )

        element_b_price_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_element_b_price
        )
        self.log.debug(
            "element b unit rate (active b price)",
            value=element_b_price_rec.value,
            serial=serial,
        )

        element_b_tou_rate_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_element_b_tou_rate
        )
        self.log.debug(
            "element b tou rate index (0-3)",
            value=element_b_tou_rate_rec.value,
            serial=serial,
        )

        emergency_credit_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_prepayment_emergency_credit
        )
        self.log.debug(
            "emergency credit", value=emergency_credit_rec.value, serial=serial
        )

        ecredit_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_prepayment_ecredit_availability
        )
        self.log.debug("ecredit", value=ecredit_rec.value, serial=serial)

        debt_recovery_rec = self._read_element(
            serial, ObjectIdEnum.tariff_active_prepayment_debt_recovery_rate
        )
        self.log.debug(
            "debt recovery rate", value=debt_recovery_rec.value, serial=serial
        )

        tariffs = TariffsActive(
            standing_charge=str(emop_scale_price_amount(standing_charge_rec.value)),
            threshold_mask=self._pluck_keys(threshold_mask_rec, "rate"),
            threshold_values=self._pluck_keys(threshold_values_rec, "th"),
            unit_rate_element_a=str(emop_scale_price_amount(active_price_rec.value)),
            unit_rate_element_b=str(emop_scale_price_amount(element_b_price_rec.value)),
            prepayment_debt_recovery_rate=str(
                emop_scale_price_amount(debt_recovery_rec.value)
            ),
            prepayment_ecredit_availability=str(
                emop_scale_price_amount(ecredit_rec.value)
            ),
            prepayment_emergency_credit=str(
                emop_scale_price_amount(emergency_credit_rec.value)
            ),
            block_rate=block_rate_rec.value,
            tou_rate=None,
            price_current=None,
            element_b_tou_rate=element_b_tou_rate_rec.value,
            element_b_block_rate=None,
            element_b_tou_rate_1=None,
            element_b_tou_rate_2=None,
            element_b_tou_rate_3=None,
            element_b_tou_rate_4=None,
            element_b_price_index_current=None,
            price_index_current=None,
            pricings=None,
            gas=None,
        )

        self.log.info("active tariffs", result=tariffs, serial=serial)

        return tariffs

    def tariffs_future_read(self, serial: str) -> TariffsFuture:
        standing_charge_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_standing_charge
        )
        self.log.debug(
            "standing charge", value=standing_charge_rec.value, serial=serial
        )

        activation_timestamp_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_activation_datetime
        )
        self.log.debug(
            "activation timestamp", value=activation_timestamp_rec.value, serial=serial
        )

        threshold_mask_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_threshold_mask
        )
        threshold_values_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_threshold_values
        )
        self._log_thresholds(threshold_mask_rec, threshold_values_rec)

        block_8_rate_1_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_block_8_rate_1
        )
        self.log.debug(
            "unit_rate_element_a (set on block 8, rate 1)",
            value=block_8_rate_1_rec.value,
            serial=serial,
        )

        element_b_tou_rate_1_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_element_b_tou_rate_1
        )
        self.log.debug(
            "unit_rate_element_b (set on tou rate 1)",
            value=element_b_tou_rate_1_rec.value,
            serial=serial,
        )

        emergency_credit_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_prepayment_emergency_credit
        )
        self.log.debug(
            "emergency credit", value=emergency_credit_rec.value, serial=serial
        )

        ecredit_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_prepayment_ecredit_availability
        )
        self.log.debug("ecredit", value=ecredit_rec.value, serial=serial)

        debt_recovery_rec = self._read_element(
            serial, ObjectIdEnum.tariff_future_prepayment_debt_recovery_rate
        )
        self.log.debug(
            "debt recovery rate", value=debt_recovery_rec.value, serial=serial
        )

        tariffs = TariffsFuture(
            standing_charge=str(emop_scale_price_amount(standing_charge_rec.value)),
            activation_datetime=emop_epoch_seconds_to_datetime(
                activation_timestamp_rec.value
            ).isoformat(timespec="seconds"),
            threshold_mask=self._pluck_keys(threshold_mask_rec, "rate"),
            threshold_values=self._pluck_keys(threshold_values_rec, "th"),
            unit_rate_element_a=str(emop_scale_price_amount(block_8_rate_1_rec.value)),
            unit_rate_element_b=str(
                emop_scale_price_amount(element_b_tou_rate_1_rec.value)
            ),
            prepayment_debt_recovery_rate=str(
                emop_scale_price_amount(debt_recovery_rec.value)
            ),
            prepayment_ecredit_availability=str(
                emop_scale_price_amount(ecredit_rec.value)
            ),
            prepayment_emergency_credit=str(
                emop_scale_price_amount(emergency_credit_rec.value)
            ),
            pricings=None,
            element_b_tou_rate_1=None,
            element_b_tou_rate_2=None,
            element_b_tou_rate_3=None,
            element_b_tou_rate_4=None,
        )

        self.log.info("future tariffs", result=tariffs, serial=serial)

        return tariffs

    def tariffs_future_write(
        self,
        serial: str,
        from_ts: datetime.datetime,
        standing_charge: Decimal,
        unit_rate: Decimal,
        emergency_credit: Decimal,
        ecredit_availability: Decimal,
        debt_recovery_rate: Decimal,
    ) -> None:
        # block threshold mask and values - set values to zeros and rate 1 only in mask
        threshold_mask_bytes = bytes(1)
        self.log.debug("zero out threshold mask")
        self._write_element(
            serial, ObjectIdEnum.tariff_future_threshold_mask, threshold_mask_bytes
        )

        threshold_values_bytes = bytes(14)
        self.log.debug("zero out threshold values")
        self._write_element(
            serial, ObjectIdEnum.tariff_future_threshold_values, threshold_values_bytes
        )

        self.log.debug("switch off tou flag")
        self._write_element(serial, ObjectIdEnum.tariff_future_tou_flag, bytes(1))

        unit_rate_encoded = emop_encode_amount_as_u4le_rec(unit_rate)

        self.log.debug(f"set element a unit rate (on block 8, rate 1) to {unit_rate}")
        self._write_element(
            serial, ObjectIdEnum.tariff_future_block_8_rate_1, unit_rate_encoded
        )

        self.log.debug(f"set element b unit rate (on tou rate 1) to {unit_rate}")
        self._write_element(
            serial, ObjectIdEnum.tariff_future_element_b_tou_rate_1, unit_rate_encoded
        )

        # prepayment amounts
        self.log.debug(
            f"set prepayment amounts [emergency_credit={emergency_credit}, ecredit_availability={ecredit_availability}, debt_recovery_rate={debt_recovery_rate}]"
        )
        self._write_element(
            serial,
            ObjectIdEnum.tariff_future_prepayment_emergency_credit,
            emop_encode_amount_as_u4le_rec(emergency_credit),
        )
        self._write_element(
            serial,
            ObjectIdEnum.tariff_future_prepayment_ecredit_availability,
            emop_encode_amount_as_u4le_rec(ecredit_availability),
        )
        self._write_element(
            serial,
            ObjectIdEnum.tariff_future_prepayment_debt_recovery_rate,
            emop_encode_amount_as_u4le_rec(debt_recovery_rate),
        )

        # gas tariff - set to zero as it doesn't apply
        self.log.debug("set gas rate to zero")
        self._write_element(serial, ObjectIdEnum.tariff_future_gas, bytes(4))

        # standing charge (daily charge)
        self.log.debug(f"set standing charge to {standing_charge}")
        self._write_element(
            serial,
            ObjectIdEnum.tariff_future_standing_charge,
            emop_encode_amount_as_u4le_rec(standing_charge),
        )

        # datetime to activate these tariffs
        self.log.debug(f"set activation date to {from_ts}")
        self._write_element(
            serial,
            ObjectIdEnum.tariff_future_activation_datetime,
            emop_encode_timestamp_as_u4le_rec(from_ts),
        )

    def tariffs_time_switches_element_a_or_single_read(self, serial: str) -> bytes:
        data = self._read_element(
            serial, ObjectIdEnum.tariff_time_switch_element_a_or_single
        )
        self.log.info(
            "element A switch settings", value=data.switch_settings, serial=serial
        )
        return cast(bytes, data.switch_settings)

    def tariffs_time_switches_element_a_or_single_write(self, serial: str) -> None:
        self._tariffs_time_switches_write(
            serial, ObjectIdEnum.tariff_time_switch_element_a_or_single
        )

    def tariffs_time_switches_element_b_read(self, serial: str) -> bytes:
        data = self._read_element(serial, ObjectIdEnum.tariff_time_switch_element_b)
        self.log.info(
            "element B switch settings", value=data.switch_settings, serial=serial
        )
        return cast(bytes, data.switch_settings)

    def tariffs_time_switches_element_b_write(self, serial: str) -> None:
        self._tariffs_time_switches_write(
            serial, ObjectIdEnum.tariff_time_switch_element_b
        )

    def _tariffs_time_switches_write(
        self, serial: str, object_id: ObjectIdEnum
    ) -> None:
        payload = bytes(80)  # all switches off - all zeros
        self._write_element(serial, object_id, payload)

    def _tariffs_pricing_blocks_read(
        self, serial: str, is_active: bool
    ) -> PricingTable:
        # create a pricings table with all values initialised to Decimal zero
        pricings: PricingTable = [[Decimal("0") for _ in range(8)] for _ in range(8)]

        for block in range(1, 9):
            for rate in range(1, 9):
                object_id_str = f"tariff_{'active' if is_active else 'future'}_block_{block}_rate_{rate}"
                price_rec = self._read_element(serial, ObjectIdEnum[object_id_str])
                self.log.debug(f"{object_id_str}={price_rec.value}", serial=serial)
                pricings[block - 1][rate - 1] = emop_scale_price_amount(price_rec.value)

        return pricings

    def _log_thresholds(
        self,
        threshold_mask: EmopMessage.TariffThresholdMaskRec,
        threshold_values: EmopMessage.TariffThresholdValuesRec,
    ) -> None:
        self.log.info(
            f"threshold mask [1={threshold_mask.rate1} 2={threshold_mask.rate2} 3={threshold_mask.rate3} 4={threshold_mask.rate4} 5={threshold_mask.rate5} 6={threshold_mask.rate6} 7={threshold_mask.rate7} 8={threshold_mask.rate8}]"
        )
        self.log.info(
            f"threshold values [1={threshold_values.th1} 2={threshold_values.th2} 3={threshold_values.th3} 4={threshold_values.th4} 5={threshold_values.th5} 6={threshold_values.th6} 7={threshold_values.th7}]"
        )

    def _pluck_keys(
        self,
        rec: EmopMessage.TariffThresholdMaskRec | EmopMessage.TariffThresholdValuesRec,
        key_prefix: str,
    ) -> Dict[str, Any]:
        return {k: v for k, v in vars(rec).items() if k.startswith(key_prefix)}
